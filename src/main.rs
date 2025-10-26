use axum::{Router, extract::Path, http::StatusCode, response::IntoResponse, routing::get};
use tokio::net::TcpListener;

#[derive(Debug)]
enum MyErr {
    NoAdapter,                 // 404
    UrlDecodeError,            // 422
    AdapterSpawnError,         // 500
    AdapterExecError,          // 500
    EnvDecodeError,            // 500
    AdapterError(u16, String), // other
}

impl IntoResponse for MyErr {
    fn into_response(self) -> axum::response::Response {
        match self {
            MyErr::NoAdapter => (
                StatusCode::NOT_FOUND,
                String::from("No adapter found for this website\n"),
            ),
            MyErr::UrlDecodeError => (
                StatusCode::UNPROCESSABLE_ENTITY,
                String::from("Could not decode URL\n"),
            ),
            MyErr::AdapterSpawnError => (
                StatusCode::INTERNAL_SERVER_ERROR,
                String::from("Could not spawn adapter process\n"),
            ),
            MyErr::AdapterExecError => (
                StatusCode::INTERNAL_SERVER_ERROR,
                String::from("Could not execute adapter\n"),
            ),
            MyErr::EnvDecodeError => (
                StatusCode::INTERNAL_SERVER_ERROR,
                String::from("Could not read .env file\n")
            ),
            MyErr::AdapterError(c, m) => (
                StatusCode::from_u16(c).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
                m,
            ),
        }
        .into_response()
    }
}

async fn refresh_bridge(Path(url): Path<String>) -> Result<String, MyErr> {
    let decoded = url::Url::parse(
        urlencoding::decode(&url)
            .map_err(|_| MyErr::UrlDecodeError)?
            .as_ref(),
    )
    .map_err(|_| MyErr::UrlDecodeError)?;

    let rev_url = decoded
        .host()
        .ok_or(MyErr::UrlDecodeError)?
        .to_string()
        .split('.')
        .rev()
        .collect::<Vec<&str>>()
        .join(",");

    let adapter = std::fs::read_dir("./adapters")
        .expect("could not open adapters directory")
        .find(|x| {
            if let Ok(f) = x {
                f.file_name().to_str().unwrap().split(".").next() == Some(&rev_url)
            } else {
                false
            }
        })
        .ok_or(MyErr::NoAdapter)?
        .unwrap();
    
    let env_vars = std::fs::read_dir("./env")
        .expect("could not open env vars directory")
        .find(|x| {
            if let Ok(f) = x {
                f.file_name().to_str().unwrap().split(".").next() == Some(&rev_url)
            } else {
                false
            }
        })
        .map(|x| {
            let buf = std::fs::read_to_string(x.unwrap().path()).or(Err(MyErr::EnvDecodeError))?;

            let mut vars = std::collections::HashMap::new();

            for dec in buf.split("\n") {
                let (name, value) = dec.split_once('=').ok_or(MyErr::EnvDecodeError)?;
                vars.insert(name.to_owned(), value.to_owned());
            };

            Ok(vars)
        })
        .transpose()?;

    let adapted;
    if let Some(env) = env_vars{
        adapted = std::process::Command::new("python3")
        .arg(adapter.path())
        .arg(decoded.as_str())
        .stdout(std::process::Stdio::piped())
        .envs(&env)
        .spawn()
        .map_err(|e| {
            dbg!(e);
            MyErr::AdapterSpawnError
        })?
        .wait_with_output()
        .map_err(|e| {
            dbg!(e);
            MyErr::AdapterExecError
        })?;  
    } else {
        adapted = std::process::Command::new("python3")
        .arg(adapter.path())
        .arg(decoded.as_str())
        .stdout(std::process::Stdio::piped())
        .spawn()
        .map_err(|e| {
            dbg!(e);
            MyErr::AdapterSpawnError
        })?
        .wait_with_output()
        .map_err(|e| {
            dbg!(e);
            MyErr::AdapterExecError
        })?;   
    }

    let output = str::from_utf8(&adapted.stdout)
        .map_err(|e| {
            dbg!(e);
            MyErr::AdapterError(500_u16, String::from("Adapter returned malformed UTF-8"))
        })?
        .to_owned();

    if !adapted.status.success() {
        if let Some(code) = adapted.status.code() {
            return Err(MyErr::AdapterError(code as u16, output));
        } else {
            return Err(MyErr::AdapterError(
                500,
                String::from("Adapter terminated through signal"),
            ));
        }
    }
    Ok(output)
}

#[tokio::main]
async fn main() {
    let app = Router::new().route("/v0/bridge/{url}", get(refresh_bridge));

    let listener = TcpListener::bind(std::env::args().nth(1).expect("Address not specified"))
        .await
        .unwrap();

    axum::serve(listener, app).await.unwrap();
}

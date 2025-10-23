from dataclasses import dataclass, field
from typing import List, Optional
from lxml import etree # pyright: ignore[reportAttributeAccessIssue]


@dataclass
class CategoryElem:
    title: str
    domain: Optional[str] = None

    def to_element(self) -> etree._Element:
        el = etree.Element("category")
        if self.domain is not None:
            el.set("domain", self.domain)
        el.text = self.title
        return el


@dataclass
class SourceElem:
    title: str
    url: Optional[str] = None

    def to_element(self) -> etree._Element:
        el = etree.Element("source")
        if self.url:
            el.set("url", self.url)
        el.text = self.title
        return el


@dataclass
class EnclosureElem:
    url: str
    length: int
    type_: str  # MIME type

    def to_element(self) -> etree._Element:
        el = etree.Element("enclosure")
        el.set("url", self.url)
        el.set("length", str(self.length))
        el.set("type", self.type_)
        return el


@dataclass
class ImageElem:
    url: str
    title: str
    link: str
    width: Optional[int] = None
    height: Optional[int] = None
    description: Optional[str] = None

    def __post_init__(self):
        """
        Validates this element is valid RSS.
        """
        if self.width is not None and self.width > 144:
            raise ValueError("image width must be at most 144")
        
        if self.height is not None and self.height > 400:
            raise ValueError("image height must be at most 400")


    def to_element(self) -> etree._Element:
        img = etree.Element("image")

        url_el = etree.SubElement(img, "url")
        url_el.text = self.url

        title_el = etree.SubElement(img, "title")
        title_el.text = self.title

        link_el = etree.SubElement(img, "link")
        link_el.text = self.link

        if self.width is not None:
            w = etree.SubElement(img, "width")
            w.text = str(self.width)
        if self.height is not None:
            h = etree.SubElement(img, "height")
            h.text = str(self.height)
        if self.description is not None:
            d = etree.SubElement(img, "description")
            d.text = self.description
        return img


@dataclass
class Item:
    title: Optional[str] = None
    link: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    comments: Optional[str] = None
    enclosure: Optional[EnclosureElem] = None
    guid: Optional[str] = None
    pub_date: Optional[str] = None
    source: Optional[SourceElem] = None

    def __post_init__(self):
        """
        Validates this element is valid RSS.
        """
        if self.title is None and self.description is None:
            raise ValueError("At least one of title or description must be present")

    def to_element(self) -> etree._Element:
        item = etree.Element("item")

        def add_text(tag: str, text: Optional[str]) -> None:
            if text is None: # no-op on undefined attributes
                return
            el = etree.SubElement(item, tag)
            el.text = str(text)

        add_text("title", self.title)
        add_text("link", self.link)
        add_text("description", self.description)
        add_text("author", self.author)
        add_text("category", self.category)
        add_text("comments", self.comments)
        if self.enclosure is not None:
            item.append(self.enclosure.to_element())
        add_text("guid", self.guid)
        add_text("pubDate", self.pub_date)
        if self.source is not None:
            item.append(self.source.to_element())

        return item


@dataclass
class RSS:
    title: str
    link: str
    description: str
    version: float = 2.0
    language: Optional[str] = None
    copyright_: Optional[str] = None
    managing_editor: Optional[str] = None
    web_master: Optional[str] = None
    pub_date: Optional[str] = None  # RFC 822 date
    last_build_date: Optional[str] = None  # RFC 822 date
    category: Optional[CategoryElem] = None
    generator: Optional[str] = None
    ttl: Optional[int] = None
    image: Optional[ImageElem] = None
    items: List[Item] = field(default_factory=list)

    def add_item(self, item: Item) -> None:
        self.items.append(item)

    def to_element(self) -> etree._Element:
        rss_el = etree.Element("rss", version=str(self.version))
        channel = etree.SubElement(rss_el, "channel")

        def add_text(parent: etree._Element, tag: str, text: Optional[str | int]) -> None:
            if text is None: # no-op for unset optional fields
                return
            el = etree.SubElement(parent, tag)
            el.text = str(text)

        add_text(channel, "title", self.title)
        add_text(channel, "link", self.link)
        add_text(channel, "description", self.description)
        add_text(channel, "language", self.language)
        add_text(channel, "copyright", self.copyright_)
        add_text(channel, "managingEditor", self.managing_editor)
        add_text(channel, "webMaster", self.web_master)
        add_text(channel, "pubDate", self.pub_date)
        add_text(channel, "lastBuildDate", self.last_build_date)
        if self.category is not None:
            channel.append(self.category.to_element())
        add_text(channel, "generator", self.generator)
        if self.ttl is not None:
            add_text(channel, "ttl", self.ttl)
        if self.image is not None:
            channel.append(self.image.to_element())
        for it in self.items:
            channel.append(it.to_element())

        return rss_el

    def to_xml_string(
        self, pretty: bool = True, xml_declaration: bool = True
    ) -> str:
        el = self.to_element()
        return etree.tostring(
            el, pretty_print=pretty, xml_declaration=xml_declaration, encoding="utf-8"
        ).decode(encoding="utf-8")

class RSSBuilder:
    """Fluent builder for RSS."""

    def __init__(self, title: str, link: str, description: str):
        self._title = title
        self._link = link
        self._description = description
        self._version: float = 2.0
        self._language: Optional[str] = None
        self._copyright: Optional[str] = None
        self._managing_editor: Optional[str] = None
        self._web_master: Optional[str] = None
        self._pub_date: Optional[str] = None
        self._last_build_date: Optional[str] = None
        self._category: Optional[CategoryElem] = None
        self._generator: str = "neath 0.2.0"
        self._ttl: Optional[int] = None
        self._image: Optional[ImageElem] = None
        self._items: List[Item] = []

    def version(self, v: float) -> "RSSBuilder":
        self._version = v
        return self

    def language(self, lang: str) -> "RSSBuilder":
        self._language = lang
        return self

    def copyright(self, c: str) -> "RSSBuilder":
        self._copyright = c
        return self

    def managing_editor(self, me: str) -> "RSSBuilder":
        self._managing_editor = me
        return self

    def web_master(self, wm: str) -> "RSSBuilder":
        self._web_master = wm
        return self

    def pub_date(self, d: str) -> "RSSBuilder":
        self._pub_date = d
        return self

    def last_build_date(self, d: str) -> "RSSBuilder":
        self._last_build_date = d
        return self

    def category(self, c: CategoryElem) -> "RSSBuilder":
        self._category = c
        return self

    def generator(self, g: str) -> "RSSBuilder":
        self._generator = g
        return self

    def ttl(self, t: int) -> "RSSBuilder":
        self._ttl = t
        return self

    def image(self, img: ImageElem) -> "RSSBuilder":
        self._image = img
        return self

    def add_item(self, item: Item) -> "RSSBuilder":
        self._items.append(item)
        return self

    def build(self) -> RSS:
        return RSS(
            title=self._title,
            link=self._link,
            description=self._description,
            version=self._version,
            language=self._language,
            copyright_=self._copyright,
            managing_editor=self._managing_editor,
            web_master=self._web_master,
            pub_date=self._pub_date,
            last_build_date=self._last_build_date,
            category=self._category,
            generator=self._generator,
            ttl=self._ttl,
            image=self._image,
            items=list(self._items),
        )
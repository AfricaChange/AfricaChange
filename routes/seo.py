"""Public discovery endpoints with an explicitly approved page allowlist."""

from xml.etree.ElementTree import Element, SubElement, tostring

from flask import Blueprint, Response, url_for


seo = Blueprint("seo", __name__)
PUBLIC_ORIGIN = "https://www.africachangex.com"
SITEMAP_ENDPOINTS = (
    "main.accueil",
    "legal.privacy",
    "legal.cgu",
    "legal.mentions",
)


@seo.route("/sitemap.xml")
def sitemap():
    root = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for endpoint in SITEMAP_ENDPOINTS:
        entry = SubElement(root, "url")
        SubElement(entry, "loc").text = PUBLIC_ORIGIN + url_for(endpoint, _external=False)
    return Response(
        tostring(root, encoding="utf-8", xml_declaration=True),
        content_type="application/xml; charset=utf-8",
    )


@seo.route("/robots.txt")
def robots():
    return Response(
        "User-agent: *\nAllow: /\n\n"
        f"Sitemap: {PUBLIC_ORIGIN}/sitemap.xml\n",
        content_type="text/plain; charset=utf-8",
    )

"""The IndexNow ping after the website's build (scripts/indexnow_ping.py): which articles count as changed."""
from scripts import indexnow_ping as ip


def doc(*posts):
    return {"posts": list(posts)}


def test_new_changed_and_removed_articles_count_but_view_counts_do_not():
    old = doc({"slug": "a", "updatedAt": "1", "views": 3}, {"slug": "b", "updatedAt": "1"}, {"slug": "c", "updatedAt": "1"})
    new = doc({"slug": "a", "updatedAt": "1", "views": 9}, {"slug": "b", "updatedAt": "2"}, {"slug": "d", "updatedAt": "1"})
    assert ip.changed(old, new) == ["b", "c", "d"]
    assert ip.changed(new, new) == []


def test_urls_both_editions_and_the_lists():
    new = doc({"slug": "b", "body_en": "x"}, {"slug": "s"})
    u = ip.urls(["b", "s", "gone"], new, site="https://x.se")
    assert u[:4] == ["https://x.se/artiklar/b/", "https://x.se/en/artiklar/b/", "https://x.se/artiklar/s/",
                     "https://x.se/artiklar/gone/"]
    assert "https://x.se/en/artiklar/s/" not in u  # no English edition
    assert "https://x.se/en/artiklar/gone/" in u  # removed: both editions are gone
    assert u[-1] == "https://x.se/sitemap.xml"


def test_the_key_file_is_in_the_public_folder():
    k = ip.key()
    assert len(k) == 32

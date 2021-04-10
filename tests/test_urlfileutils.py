class TestUrlFileUtils01:
    def test_urlfileutils01m01(self):
        """
        Unit test method (make linter happy)
        """
        from gatenlp.urlfileutils import is_url
        import urllib
        import pathlib

        isu, ext = is_url("somefile")
        assert not isu
        assert ext == "somefile"

        isu, ext = is_url("/some/other/file")
        assert not isu
        assert ext == "/some/other/file"

        isu, ext = is_url(pathlib.Path("http://somewhere.org/x"))
        assert not isu
        assert ext == "http:/somewhere.org/x"

        isu, ext = is_url("file:///somewhere.org/x")
        assert not isu
        assert ext == "/somewhere.org/x"

        isu, ext = is_url(urllib.parse.urlparse("file:///somewhere.org/x"))
        assert isu
        assert ext == "file:///somewhere.org/x"

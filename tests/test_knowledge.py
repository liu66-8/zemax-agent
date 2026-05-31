from zemax_agent.knowledge.glass_library import GlassLibrary, GlassMaterial, PRESET_GLASS_CATALOG


class TestGlassLibrary:
    def test_preset_catalog_loaded(self):
        lib = GlassLibrary()
        assert len(lib) >= 30

    def test_get_glass(self):
        lib = GlassLibrary()
        g = lib.get("N-BK7")
        assert g is not None
        assert g.refractive_index_nd == 1.51680
        assert g.abbe_number_vd == 64.17

    def test_get_case_insensitive(self):
        lib = GlassLibrary()
        g = lib.get("n-bk7")
        assert g is not None
        assert g.manufacturer == "Schott"

    def test_query_nd_range(self):
        lib = GlassLibrary()
        results = lib.query(nd_min=1.7, nd_max=1.8)
        assert len(results) > 0
        for g in results:
            assert 1.7 <= g.refractive_index_nd <= 1.8

    def test_query_manufacturer(self):
        lib = GlassLibrary()
        results = lib.query(manufacturer="CDGM")
        assert len(results) > 0
        for g in results:
            assert g.manufacturer == "CDGM"

    def test_query_vd_range(self):
        lib = GlassLibrary()
        results = lib.query(vd_min=70)
        assert len(results) > 0
        for g in results:
            assert g.abbe_number_vd >= 70

    def test_query_cost(self):
        lib = GlassLibrary()
        results = lib.query(max_cost=1.0)
        for g in results:
            assert g.cost_factor <= 1.0

    def test_search_text(self):
        lib = GlassLibrary()
        results = lib.search_text("BK7")
        assert len(results) >= 1

    def test_get_manufacturers(self):
        lib = GlassLibrary()
        manufacturers = lib.get_manufacturers()
        assert "Schott" in manufacturers

    def test_recommend_alternatives(self):
        lib = GlassLibrary()
        alternatives = lib.recommend_alternatives("N-BK7")
        assert len(alternatives) > 0
        for g in alternatives:
            assert g.name != "N-BK7"

    def test_to_search_texts(self):
        lib = GlassLibrary()
        texts = lib.to_search_texts()
        assert len(texts) == len(lib)
        assert "N-BK7" in texts[0]

    def test_add_custom_glass(self):
        lib = GlassLibrary()
        custom = GlassMaterial(name="CUSTOM-1", manufacturer="Custom", refractive_index_nd=1.65, abbe_number_vd=45.0)
        lib.add(custom)
        assert lib.get("CUSTOM-1") is not None

    def test_nd_vd_range(self):
        lib = GlassLibrary()
        ranges = lib.get_nd_vd_range()
        assert ranges["nd"][0] > 1.0
        assert ranges["vd"][0] > 20

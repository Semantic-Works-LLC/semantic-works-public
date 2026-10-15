"""js/rng.js: seeded random numbers and the distributions drawn from them."""
import pytest


def test_the_same_seed_gives_the_same_numbers(page):
    a, b, c = page.evaluate("[1, 1, 2].map(seed => { const r = new Rng(seed); return [r.next(), r.next(), r.next()]; })")
    assert a == b and a != c and all(0 <= x < 1 for x in a)


def test_a_zero_seed_is_made_usable(page):
    assert page.evaluate("new Rng(0).s") == 1


def test_stream_seeds_differ_by_name_and_by_seed_and_are_never_zero(page):
    names = ["des:arrival", "des:size", "des:order", "des:menu", "des:run", "des:dine", "des:orderPatience", "des:foodPatience"]
    one, two = page.evaluate("names => [1, 2].map(seed => names.map(name => streamSeed(seed, name)))", names)
    assert len(set(one)) == len(names), "every stream of one run has its own seed"
    assert all(a != b for a, b in zip(one, two)), "another run seed moves every stream"
    assert all(one + two) and page.evaluate("streamSeed(1, 'des:order') === streamSeed(1, 'des:order')")


def test_uniform_stays_in_range(page):
    assert page.evaluate("(() => { const r = new Rng(7); return Array.from({ length: 500 }, () => r.uniform(5, 10)).every(x => x >= 5 && x < 10); })()")


def test_triangular_stays_in_range_and_leans_to_its_mode(page):
    low, high, mean = page.evaluate("""() => {
        const r = new Rng(7), xs = Array.from({ length: 4000 }, () => r.triangular(4, 6, 9));
        return [Math.min(...xs), Math.max(...xs), xs.reduce((a, b) => a + b) / xs.length];
    }""")
    assert 4 <= low and high <= 9 and mean == pytest.approx((4 + 6 + 9) / 3, abs=0.15)


def test_triangular_with_no_width_is_that_value(page):
    assert page.evaluate("new Rng(3).triangular(5, 5, 5)") == 5


def test_draw_takes_a_number_or_a_distribution(page):
    drawn = page.evaluate("""() => { const r = new Rng(9);
        return [r.draw(2), r.draw({ dist: 'uniform', min: 1, max: 2 }), r.draw({ dist: 'triangular', min: 1, mode: 2, max: 3 })]; }""")
    assert drawn[0] == 2 and 1 <= drawn[1] < 2 and 1 <= drawn[2] <= 3


def test_draw_refuses_an_unknown_distribution(page):
    assert "unknown distribution" in page.evaluate("(() => { try { new Rng(1).draw({ dist: 'gamma' }); } catch (e) { return e.message; } })()")


def test_a_stream_seed_that_would_come_out_as_zero_is_made_one(page):
    """Found by searching: with this run seed the mix of the name "x" is exactly zero, which the generator could not use."""
    assert page.evaluate("streamSeed(2166136253, 'x')") == 1

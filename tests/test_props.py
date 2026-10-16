"""Arena props: the Stand grabs one (Pose), throws it (Pose again); back in place later."""

from helpers import NONE, kinds, press, run

from jojo_arena.characters import get_fighter
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Vec2
from jojo_arena.stages import load_stage

RULES = load_rules()


def cairo(p1=(120, 92), p2=(300, 92), who="jotaro_p3"):
    """A fight in the Cairo street, player 1 next to the crate at (120, 70)."""
    arena = load_stage("cairo_night").build_arena()
    kits = (get_fighter(who).kit, get_fighter("dio_p3").kit)
    match = Match(kits, RULES, arena)
    match.fighters[0].pos, match.fighters[1].pos = Vec2(*p1), Vec2(*p2)
    return match


def crate(match):
    return next(o for o in match.arena.obstacles if o.kind == "crate")


def test_pose_near_a_prop_picks_it_up():
    match = cairo()
    events = run(match, 2, p1=press("pose"))
    assert "pickup" in kinds(events)
    assert match.fighters[0].carrying is not None
    assert crate(match).carried_by == 0 and not crate(match).solid
    assert match.fighters[0].state.name != "POSE"


def test_pose_away_from_props_is_still_the_pose():
    match = cairo(p1=(240, 150))
    match.step((press("pose", hold=("pose",)), NONE))
    assert match.fighters[0].carrying is None
    assert match.fighters[0].state.name == "POSE"


def test_pose_again_throws_the_prop_and_it_breaks_on_the_opponent():
    match = cairo(p2=(200, 92))
    run(match, 2, p1=press("pose"))
    dio = match.fighters[1]
    events = run(match, 60, p1=press("pose"))
    assert "throw" in kinds(events)
    power = match.fighters[0].kit.strength
    assert dio.hp == dio.max_hp - round(crate(match).throw_damage * power)
    assert crate(match).broken
    assert match.fighters[0].carrying is None


def test_while_the_stand_holds_it_the_user_fights_as_usual():
    match = cairo()
    run(match, 2, p1=press("pose"))
    match.step((press("light"), NONE))
    assert match.fighters[0].attack is not None  # a normal jab...
    assert match.fighters[0].carrying is not None  # ...and the Stand still holds it


def test_a_strong_stand_throws_much_harder():
    def throw(who):
        match = cairo(p2=(330, 92), who=who)
        run(match, 2, p1=press("pose"))
        run(match, 1, p1=press("pose"))
        return next(p for p in match.projectiles if p.prop is not None).defn

    strong, weak = throw("jotaro_p3"), throw("kakyoin")
    assert strong.speed > weak.speed * 1.8
    assert strong.damage > weak.damage * 1.8
    assert strong.wall_bounce and not weak.wall_bounce


def test_a_broken_prop_comes_back_home():
    match = cairo(p2=(200, 92))
    box = crate(match)
    home = box.home
    run(match, 2, p1=press("pose"))
    run(match, 60, p1=press("pose"))
    assert box.broken and box.rect != home  # it broke over there, on DIO
    match.fighters[0].pos = Vec2(300, 200)  # nobody stands on its spot
    events = run(match, box.respawn_f + 2)
    assert "prop_respawn" in kinds(events)
    assert not box.broken and box.rect == home


def test_getting_hit_drops_it():
    match = cairo(p2=(140, 92))
    run(match, 2, p1=press("pose"))
    run(match, 30, p2=press("light"))
    assert match.fighters[0].carrying is None
    assert crate(match).solid  # fell at his feet, whole


def test_the_stand_carries_it_so_the_walk_is_unchanged():
    match = cairo()
    jotaro = match.fighters[0]
    free_speed = jotaro.walk_speed()
    run(match, 2, p1=press("pose"))
    assert jotaro.walk_speed() == free_speed

import pytest

from vink.domain.errors import LanguageUnavailableError
from vink.domain.models import TrackInfo, TrackKind
from vink.processing.track_selection import ORIGINAL_LANGUAGE, select_track

MANUAL_EN = TrackInfo("en", "English", is_generated=False, translation_codes=frozenset({"es"}))
MANUAL_PT_BR = TrackInfo("pt-BR", "Portuguese (Brazil)", is_generated=False)
AUTO_EN = TrackInfo("en", "English (auto)", is_generated=True, translation_codes=frozenset({"fr"}))
AUTO_HI = TrackInfo("hi", "Hindi (auto)", is_generated=True, translation_codes=frozenset({"en"}))
MANUAL_AR = TrackInfo("ar", "Arabic", is_generated=False)


def test_prefers_manual_over_generated() -> None:
    selection = select_track([AUTO_EN, MANUAL_EN], ["en"], video_id="v")

    assert selection.track is MANUAL_EN
    assert selection.translate_to is None


def test_uses_generated_when_no_manual_match() -> None:
    selection = select_track([MANUAL_AR, AUTO_HI], ["hi"], video_id="v")

    assert selection.track is AUTO_HI


def test_respects_language_order() -> None:
    selection = select_track([MANUAL_EN, AUTO_HI], ["hi", "en"], video_id="v")

    assert selection.track is AUTO_HI


def test_base_language_matches_region_variant() -> None:
    assert select_track([MANUAL_PT_BR], ["pt"], video_id="v").track is MANUAL_PT_BR


def test_region_variant_falls_back_to_base_language() -> None:
    assert select_track([MANUAL_EN], ["en-GB"], video_id="v").track is MANUAL_EN


def test_matching_is_case_insensitive() -> None:
    assert select_track([MANUAL_PT_BR], ["PT-br"], video_id="v").track is MANUAL_PT_BR


def test_original_means_spoken_language() -> None:
    selection = select_track([MANUAL_AR, MANUAL_EN, AUTO_HI], [ORIGINAL_LANGUAGE], video_id="v")

    assert selection.track is AUTO_HI


def test_original_without_generated_track_uses_first_track() -> None:
    assert select_track([MANUAL_AR, MANUAL_EN], ["original"], video_id="v").track is MANUAL_AR


def test_translates_when_no_track_matches_preferring_manual_source() -> None:
    selection = select_track([AUTO_EN, MANUAL_EN], ["es"], video_id="v")

    assert selection.track is MANUAL_EN
    assert selection.translate_to == "es"
    assert selection.kind is TrackKind.TRANSLATED


def test_translation_from_generated_source() -> None:
    selection = select_track([MANUAL_AR, AUTO_HI], ["en"], video_id="v")

    assert selection.track is AUTO_HI
    assert selection.translate_to == "en"


def test_raises_when_translation_disabled() -> None:
    with pytest.raises(LanguageUnavailableError) as info:
        select_track([MANUAL_EN], ["es"], video_id="v", allow_translation=False)

    assert info.value.requested == ("es",)
    assert info.value.available == ("en",)


def test_raises_when_nothing_matches() -> None:
    with pytest.raises(LanguageUnavailableError) as info:
        select_track([MANUAL_AR, AUTO_EN], ["ja"], video_id="v")

    assert info.value.available == ("ar", "en")


def test_raises_for_video_without_tracks() -> None:
    with pytest.raises(LanguageUnavailableError):
        select_track([], ["en", "original"], video_id="v")

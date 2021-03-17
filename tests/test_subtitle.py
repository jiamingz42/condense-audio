from trim_movie.subtitle import group_captions, Caption, Timestamp, CaptionGroup

import unittest


class TestSubtitle(unittest.TestCase):
    def test_group_captions_duration(self):
        group = CaptionGroup()
        group.append(Caption(Timestamp(0), Timestamp(1000), "Foo"))
        group.append(Caption(Timestamp(2000), Timestamp(3000), "Bar"))
        assert group.duration == Timestamp(3000)

    def test_group_captions_empty_captions(self):
        assert len(group_captions([], 1000)) == 0

    def test_group_captions_split_to_2_groups(self) -> None:
        captions = [
            Caption(Timestamp(0), Timestamp(1000), "Foo"),
            Caption(Timestamp(2000), Timestamp(3000), "Bar"),
        ]
        actual_groups = group_captions(captions, 500)
        expected_groups = [
            CaptionGroup([Caption(Timestamp(0), Timestamp(1000), "Foo")]),
            CaptionGroup([Caption(Timestamp(2000), Timestamp(3000), "Bar")]),
        ]
        assert len(actual_groups) == 2
        assert actual_groups == expected_groups

    def test_group_captions_split_to_1_groups(self) -> None:
        captions = [
            Caption(Timestamp(0), Timestamp(1000), "Foo"),
            Caption(Timestamp(2000), Timestamp(3000), "Bar"),
        ]
        actual_groups = group_captions(captions, 9999)
        expected_groups = [
            CaptionGroup([Caption(Timestamp(0), Timestamp(1000), "Foo"),
                          Caption(Timestamp(2000), Timestamp(3000), "Bar")]),
        ]
        assert len(actual_groups) == 1
        assert actual_groups[0].captions == expected_groups[0].captions


if __name__ == '__main__':
    unittest.main()

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from luna.core.tokenizer import CharTokenizer


def test_round_trip_small():
    text = "Xin chào Luna"
    tok = CharTokenizer(text)
    s = "chào Luna"
    assert tok.decode(tok.encode(s)) == s  # mã hóa rồi giải mã phải ra đúng chuỗi gốc


def test_round_trip_corpus():
    # Dựng tokenizer từ corpus -> biết mọi ký tự trong corpus -> mã hóa rồi giải mã phải ra đúng chuỗi gốc
    tok = CharTokenizer.from_file("data/raw/corpus.txt")
    s = "Chào cậu chủ, em là Luna. Rất vui được gặp cậu chủ. Chúc cậu chủ một ngày mới tốt lành."
    assert (
        tok.decode(tok.encode(s)) == s
    )  # corpus.txt phải chứa mọi ký tự trong s, nếu không sẽ lỗi KeyError
    assert tok.vocab_size > 100


def test_unknow_char_no_crash():
    tok = CharTokenizer("abc")
    ids = tok.encode(
        "axz"
    )  # 'x','z' lạ -> không crash, sẽ được chuyển thành ký hiệu lạ (unk) để tránh crash
    assert ids[0] == tok.stoi["a"]
    assert ids[1] == tok.unk_id
    assert (
        tok.decode(ids) == "a��"
    )  # 'a' giữ nguyên, những ký hiệu lạ sẽ được chuyển thành �� để tránh gây crash

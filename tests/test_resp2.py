import unittest

from network.resp2 import (
    RESPProtocolError,
    bulk_string,
    error_response,
    integer,
    parse_request,
    simple_string,
)


class ParseRequestTests(unittest.TestCase):
    def test_parses_complete_command(self):
        frame = b"*2\r\n$3\r\nGET\r\n$4\r\nname\r\n"

        command, remaining = parse_request(frame)

        self.assertEqual(command, [b"GET", b"name"])
        self.assertEqual(remaining, b"")

    def test_returns_none_for_fragmented_command(self):
        frame = b"*2\r\n$3\r\nGET\r\n$4\r\nna"

        self.assertIsNone(parse_request(frame))

    def test_preserves_pipelined_command(self):
        first = b"*1\r\n$4\r\nPING\r\n"
        second = b"*2\r\n$3\r\nGET\r\n$4\r\nname\r\n"

        command, remaining = parse_request(first + second)

        self.assertEqual(command, [b"PING"])
        self.assertEqual(remaining, second)

    def test_bulk_string_can_contain_spaces_and_newlines(self):
        value = b"hello\r\nworld"
        frame = (
            b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n"
            + f"${len(value)}\r\n".encode("ascii")
            + value
            + b"\r\n"
        )

        command, remaining = parse_request(frame)

        self.assertEqual(command, [b"SET", b"key", value])
        self.assertEqual(remaining, b"")

    def test_rejects_non_array_request(self):
        with self.assertRaises(RESPProtocolError):
            parse_request(b"+PING\r\n")

    def test_rejects_invalid_bulk_length(self):
        with self.assertRaises(RESPProtocolError):
            parse_request(b"*1\r\n$nope\r\nPING\r\n")

    def test_rejects_invalid_array_length(self):
        with self.assertRaises(RESPProtocolError):
            parse_request(b"*nope\r\n")

    def test_rejects_empty_array(self):
        with self.assertRaises(RESPProtocolError):
            parse_request(b"*0\r\n")

    def test_rejects_negative_array_length(self):
        with self.assertRaises(RESPProtocolError):
            parse_request(b"*-1\r\n")

    def test_rejects_null_bulk_argument(self):
        with self.assertRaises(RESPProtocolError):
            parse_request(b"*1\r\n$-1\r\n")

    def test_rejects_non_bulk_array_element(self):
        with self.assertRaises(RESPProtocolError):
            parse_request(b"*1\r\n+PING\r\n")

    def test_rejects_bulk_string_without_terminating_crlf(self):
        with self.assertRaises(RESPProtocolError):
            parse_request(b"*1\r\n$4\r\nPINGxx")

    def test_returns_none_for_fragmented_array_header(self):
        self.assertIsNone(parse_request(b"*1\r"))

    def test_returns_none_for_fragmented_bulk_payload(self):
        self.assertIsNone(parse_request(b"*1\r\n$4\r\nPIN"))


class ResponseEncodingTests(unittest.TestCase):
    def test_simple_string(self):
        self.assertEqual(simple_string("OK"), b"+OK\r\n")

    def test_integer(self):
        self.assertEqual(integer(1), b":1\r\n")

    def test_null_bulk_string(self):
        self.assertEqual(bulk_string(None), b"$-1\r\n")

    def test_bulk_length_counts_utf8_bytes(self):
        self.assertEqual(bulk_string("é"), b"$2\r\n\xc3\xa9\r\n")

    def test_error_cannot_inject_an_extra_response_line(self):
        self.assertEqual(
            error_response("bad\r\n+INJECTED"),
            b"-ERR bad  +INJECTED\r\n",
        )


if __name__ == "__main__":
    unittest.main()

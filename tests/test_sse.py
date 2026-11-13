import json

from ctxblame.sse import SSEParser, assemble_message, parse_sse


def ev(etype, **payload):
    return f"event: {etype}\ndata: {json.dumps({'type': etype, **payload})}\n\n"


TOOL_STREAM = "".join([
    ev("message_start", message={"id": "msg_1", "type": "message", "role": "assistant",
                                  "model": "m", "content": [], "stop_reason": None,
                                  "usage": {"input_tokens": 120, "output_tokens": 1}}),
    ": keep-alive comment\n\n",
    ev("content_block_start", index=0, content_block={"type": "thinking", "thinking": "", "signature": ""}),
    ev("content_block_delta", index=0, delta={"type": "thinking_delta", "thinking": "need to "}),
    ev("content_block_delta", index=0, delta={"type": "thinking_delta", "thinking": "list files"}),
    ev("content_block_delta", index=0, delta={"type": "signature_delta", "signature": "sig"}),
    ev("content_block_stop", index=0),
    ev("ping"),
    ev("content_block_start", index=1, content_block={"type": "text", "text": ""}),
    ev("content_block_delta", index=1, delta={"type": "text_delta", "text": "Let me "}),
    ev("content_block_delta", index=1, delta={"type": "text_delta", "text": "check."}),
    ev("content_block_stop", index=1),
    ev("content_block_start", index=2, content_block={"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": {}}),
    ev("content_block_delta", index=2, delta={"type": "input_json_delta", "partial_json": ""}),
    ev("content_block_delta", index=2, delta={"type": "input_json_delta", "partial_json": '{"command": "l'}),
    ev("content_block_delta", index=2, delta={"type": "input_json_delta", "partial_json": 's -la"}'}),
    ev("content_block_stop", index=2),
    ev("message_delta", delta={"stop_reason": "tool_use", "stop_sequence": None},
       usage={"output_tokens": 42, "input_tokens": 120, "cache_read_input_tokens": None}),
    ev("message_stop"),
])


def test_parser_handles_arbitrary_chunking():
    whole = parse_sse(TOOL_STREAM)
    p = SSEParser()
    pieces = []
    for i in range(0, len(TOOL_STREAM), 7):
        pieces += p.feed(TOOL_STREAM[i:i + 7].encode())
    pieces += p.flush()
    assert [e.to_json() for e in pieces] == [e.to_json() for e in whole]
    assert len(whole) == 18  # comment dropped, ping kept


def test_assemble_tool_call():
    msg = assemble_message(parse_sse(TOOL_STREAM))
    assert msg["_stream_complete"] is True
    assert msg["stop_reason"] == "tool_use"
    assert msg["usage"] == {"input_tokens": 120, "output_tokens": 42}
    assert [b["type"] for b in msg["content"]] == ["thinking", "text", "tool_use"]
    assert msg["content"][0]["thinking"] == "need to list files"
    assert msg["content"][0]["signature"] == "sig"
    assert msg["content"][1]["text"] == "Let me check."
    assert msg["content"][2] == {"type": "tool_use", "id": "toolu_1", "name": "Bash",
                                 "input": {"command": "ls -la"}}


def test_crlf_and_multiline_data():
    evs = parse_sse("event: x\r\ndata: a\r\ndata: b\r\n\r\n")
    assert evs[0].event == "x" and evs[0].data == "a\nb"


def test_truncated_stream_and_unnamed_error_frame():
    truncated = TOOL_STREAM.split("event: message_delta")[0]
    assert assemble_message(parse_sse(truncated))["_stream_complete"] is False
    err = assemble_message(parse_sse('data: {"error": {"message": "timeout"}}\n\n'))
    assert err["_stream_error"] == {"message": "timeout"}


def test_multibyte_char_split_across_chunks():
    data = 'event: x\ndata: {"t": "清理构建目录"}\n\n'.encode()
    p = SSEParser()
    out = []
    for i in range(len(data)):  # one byte at a time splits every CJK char
        out += p.feed(data[i:i + 1])
    out += p.flush()
    assert json.loads(out[0].data)["t"] == "清理构建目录"

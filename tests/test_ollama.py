import os

import psycopg
import pytest


# skip tests in this module if disabled
enable_ollama_tests = os.getenv("ENABLE_OLLAMA_TESTS")
if not enable_ollama_tests or enable_ollama_tests == "0":
    pytest.skip(allow_module_level=True)


@pytest.fixture()
def ollama_host() -> str:
    ollama_host = os.environ['OLLAMA_HOST']
    return ollama_host


@pytest.fixture()
def con(db_url) -> psycopg.Connection:
    return psycopg.connect(db_url)


@pytest.fixture()
def cur(con) -> psycopg.Cursor:
    with con:
        with con.cursor() as cursor:
            yield cursor


@pytest.fixture()
def cur_with_ollama_host(ollama_host, con) -> psycopg.Cursor:
    with con:
        with con.cursor() as cursor:
            cursor.execute("select set_config('ai.ollama_host', %s, false) is not null", (ollama_host,))
            yield cursor


def test_ollama_list_models_no_host(cur_with_ollama_host):
    cur_with_ollama_host.execute("select count(*) > 0 from ai.ollama_list_models()")
    actual = cur_with_ollama_host.fetchone()[0]
    assert actual is True


def test_ollama_list_models(cur, ollama_host):
    cur.execute("select count(*) > 0 from ai.ollama_list_models(_host=>%s)", (ollama_host,))
    actual = cur.fetchone()[0]
    assert actual is True


def test_ollama_embed(cur, ollama_host):
    cur.execute("""
        select vector_dims
        (
            ai.ollama_embed
            ( 'llama3'
            , 'the purple elephant sits on a red mushroom'
            , _host=>%s
            )
        )
    """, (ollama_host,))
    actual = cur.fetchone()[0]
    assert actual == 4096


def test_ollama_embed_no_host(cur_with_ollama_host):
    cur_with_ollama_host.execute("""
        select vector_dims
        (
            ai.ollama_embed
            ( 'llama3'
            , 'the purple elephant sits on a red mushroom'
            )
        )
    """)
    actual = cur_with_ollama_host.fetchone()[0]
    assert actual == 4096


def test_ollama_embed_via_openai(cur, ollama_host):
    cur.execute("""
        select vector_dims
        (
            ai.openai_embed
            ( 'llama3'
            , 'the purple elephant sits on a red mushroom'
            , _api_key=>'this is a garbage api key'
            , _base_url=>concat(%s::text, '/v1/')
            )
        )
    """, (ollama_host,))
    actual = cur.fetchone()[0]
    assert actual == 4096


def test_ollama_generate(cur, ollama_host):
    cur.execute("""
        select ai.ollama_generate
        ( 'llama3'
        , 'what is the typical weather like in Alabama in June'
        , _system=>'you are a helpful assistant'
        , _host=>%s
        , _options=> jsonb_build_object
          ( 'seed', 42
          , 'temperature', 0.6
          )
        )
    """, (ollama_host,))
    actual = cur.fetchone()[0]
    assert "response" in actual and "done" in actual and actual["done"] is True


def test_ollama_generate_no_host(cur_with_ollama_host):
    cur_with_ollama_host.execute("""
        select ai.ollama_generate
        ( 'llama3'
        , 'what is the typical weather like in Alabama in June'
        , _system=>'you are a helpful assistant'
        , _options=> jsonb_build_object
          ( 'seed', 42
          , 'temperature', 0.6
          )
        )
    """)
    actual = cur_with_ollama_host.fetchone()[0]
    assert "response" in actual and "done" in actual and actual["done"] is True


def test_ollama_image(cur_with_ollama_host):
    cur_with_ollama_host.execute("""
        select ai.ollama_generate
        ( 'llava:7b'
        , 'Please describe this image.'
        , _images=> array[pg_read_binary_file('/pgai/tests/postgresql-vs-pinecone.jpg')]
        , _system=>'you are a helpful assistant'
        , _options=> jsonb_build_object
          ( 'seed', 42
          , 'temperature', 0.9
          )
        )
    """)
    actual = cur_with_ollama_host.fetchone()[0]
    assert "response" in actual and "done" in actual and actual["done"] is True


def test_ollama_chat_complete(cur, ollama_host):
    cur.execute("""
        select ai.ollama_chat_complete
        ( 'llama3'
          , jsonb_build_array
          ( jsonb_build_object('role', 'system', 'content', 'you are a helpful assistant')
            , jsonb_build_object('role', 'user', 'content', 'what is the typical weather like in Alabama in June')
            )
          , _host=>%s
          , _options=> jsonb_build_object
          ( 'seed', 42
          , 'temperature', 0.6
          )
        )
    """, (ollama_host,))
    actual = cur.fetchone()[0]
    assert "message" in actual and "content" in actual["message"] and "done" in actual and actual["done"] is True


def test_ollama_chat_complete_no_host(cur_with_ollama_host):
    cur_with_ollama_host.execute("""
        select ai.ollama_chat_complete
        ( 'llama3'
          , jsonb_build_array
          ( jsonb_build_object('role', 'system', 'content', 'you are a helpful assistant')
            , jsonb_build_object('role', 'user', 'content', 'what is the typical weather like in Alabama in June')
            )
          , _options=> jsonb_build_object
          ( 'seed', 42
          , 'temperature', 0.6
          )
        )
    """)
    actual = cur_with_ollama_host.fetchone()[0]
    assert "message" in actual and "content" in actual["message"] and "done" in actual and actual["done"] is True


def test_ollama_chat_complete_image(cur_with_ollama_host):
    cur_with_ollama_host.execute("""
        select ai.ollama_chat_complete
        ( 'llava:7b'
        , jsonb_build_array
          ( jsonb_build_object
            ( 'role', 'user'
            , 'content', 'describe this image'
            , 'images', jsonb_build_array(encode(pg_read_binary_file('/pgai/tests/postgresql-vs-pinecone.jpg'), 'base64'))
            )
          )
        , _options=> jsonb_build_object
          ( 'seed', 42
          , 'temperature', 0.9
          )
        )->'message'->>'content'
    """)
    actual = cur_with_ollama_host.fetchone()[0]
    assert actual is not None


def test_ollama_ps(cur, ollama_host):
    cur.execute("""
        select count(*) filter (where "name" = 'llava:7b') as actual
        from ai.ollama_ps(_host=>%s)
    """, (ollama_host,))
    actual = cur.fetchone()[0]
    assert actual > 0


def test_ollama_ps_no_host(cur_with_ollama_host):
    cur_with_ollama_host.execute("""
        select count(*) filter (where "name" = 'llava:7b') as actual
        from ai.ollama_ps()
    """)
    actual = cur_with_ollama_host.fetchone()[0]
    assert actual > 0


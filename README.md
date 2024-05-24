# Postgres AI

Postgres AI (pgai) enables you to handle more AI workflows within a database. pgai simplifies 
the process of building [similarity search](https://en.wikipedia.org/wiki/Similarity_search), and 
[Retrieval-Augmented Generation](https://en.wikipedia.org/wiki/Prompt_engineering#Retrieval-augmented_generation) 
(RAG) apps with PostgreSQL. 

Directly from your existing PostgreSQL database, pgai empowers you to:

* Create OpenAI [embeddings](#openai_embed). 
* Retrieve OpenAI [chat completions](#openai_chat_complete) from 
  models such as GPT4o.
* Facilitate use cases such as [classification, summarization, and data enrichment](#openai_moderate) on your existing 
  relational data.

This page shows you how to set up your pgai environment, and interact with OpenAPI through your database. 

## pgai Prerequisites

Before you start working with pgai, you need:

* The pgai source on your local machine:
   ```bash
   git clone git@github.com:timescale/pgai.git
   ```
* If you prefer using Docker:
  * [Docker](https://docs.docker.com/get-docker/)
  * [Psql](https://www.timescale.com/blog/how-to-install-psql-on-mac-ubuntu-debian-windows/) or [PopSQL](https://docs.timescale.com/use-timescale/latest/popsql/)
* If you prefer a local virtual Ubuntu environment:
    * [Multipass](https://multipass.run/)
* If you prefer local development:
  *  [PostgreSQL with pgvector](https://docs.timescale.com/self-hosted/latest/install/installation-linux/#install-and-configure-timescaledb-on-postgresql) v16

     TODO: this package does not include `pgxs.mk`. Can you update the install instructions please. 

  *  [plpython3u](https://www.postgresql.org/docs/current/plpython.html)
  *  [Python3](https://www.python.org/downloads/)

## Set up your pgai developer environment

Best practice is to use the Docker environment supplied by Timescale. You can also integrate
pgai into your local developer environment. Either:

<details>
<summary>Set up a developer environment in Docker</summary>
<p></p>
The pgai Docker container has all the software you need preinstalled. To connect to
pgai running in a Docker container:


1. In Terminal, navigate to the folder you cloned pgai to. 

1. Build the Docker image:

   ```bash
   docker build -t pgai .
   ```

1. Run the container:

    ```bash
    docker run -d --name pgai -p 9876:5432 -e POSTGRES_PASSWORD=pgaipass pgai
    ```

1. Connect to the database:

    ```bash
    psql -d "postgres://postgres:pgaipass@localhost:9876/postgres"
    ```

1. Create the pgai extension:

    ```sql
    CREATE EXTENSION ai CASCADE;
    ```
   The `CASCADE` automatically installs the plpython3u and pgvector dependencies.

</details>
<details>
<summary>Set up a virtual developer environment locally</summary>
<p></p>
Best practice is to set up your developer environment in Docker. However, to install pgai in a virtual
Ubuntu environment.

In this repository, [vm.sh](./vm.sh) creates a [multipass](https://multipass.run/) virtual machine called `pgai`. This script 
installs the [pgai Prerequisites](#pgai-prerequisites) in the `pgai` Ubuntu virtual
machine. This repo is mounted to `/pgai` in the virtual machine.

1. To create the virtual machine, run the following command:

    ```bash
    ./vm.sh
    ```

    You are automatically logged into Terminal on the virtual machine.

1. In the multipass shell, [Set up a developer environment locally](#setup-a-developer-environment-locally).

For more information on using Multipass, [see the documentation](https://multipass.run/docs/use-an-instance).

</details>
<details>
<summary>Set up a developer environment locally</summary>
<a id="setup-a-developer-environment-locally"></a>
<p></p>
Best practice is to set up your developer environment in Docker. However, to install pgai directly on your 
developer environment. 

1. On the command line, navigate to the folder you cloned pgai to.

1. Build pgai:

    ```bash
    make install
    ```

    This installs the pgvector and pgai extensions on your local PostgreSQL developer
    environment, then installs the package dependencies in your Python environment.

   
1. Create the pgai extension in a database. Use either:

   - SQL:
      1. Connect to PostgreSQL:
         ```bash
         psql -d "postgres://postgres:pgaipass@localhost:9876/postgres"
         ```
         TODO: Is this true for the local installation? Is the database already created?

      1. Create the pgai extension:
   
          ```sql
          CREATE EXTENSION IF NOT EXISTS ai CASCADE;
          ```
    
          The `CASCADE` automatically installs the plpython3u and pgvector dependencies.

   - Terminal: 
     1. In `Makefile`, update `DB` and `USER` to match your PostgreSQL configuration. 
     1.  Create the pgai extension:

        ```bash
        make create_extension
        ```
</details>


## Securely connect to OpenAI through pgai

API keys are secret. Exposing them can present financial and information security issues. 
The following sections show how to securely connect to your OpenAI account through pgai using psql and Python.

### Use psql in Terminal

To securely interact with OpenAI through pgai from Terminal:

1. Set your OpenAI key as an environment variable:
    ```bash
    OPENAI_AI_KEY="this-is-my-super-secret-api-key-dont-tell"
    ```

1. Set the value of your environment variable as a [psql variable](https://www.postgresql.org/docs/current/app-psql.html#APP-PSQL-VARIABLES).
   ```bash
    psql -v OPENAI_API_KEY=$OPENAI_API_KEY
    ```
   You can now connect to your database using your psql variable as a [command line argument](https://www.postgresql.org/docs/current/app-psql.html#APP-PSQL-OPTION-VARIABLE).

1. Pass your API key as a parameterized variable when you query the database:
    ```sql
    SELECT * 
    FROM openai_list_models($1)
    ORDER BY created DESC
    \bind :OPENAI_API_KEY
    \g
    ```

    You use [bind](https://www.postgresql.org/docs/current/app-psql.html#APP-PSQL-META-COMMAND-BIND) to pass the value of `OPENAI_API_KEY` as a parameterized variable. Now, the value 
    of your API key is not visible in the query, logs, pg_stat_statements, and so on.

The `\bind` metacommand is available in psql version 16+.



### Connect through psql in a Python app

To securely interact with OpenAI in a Python app, you use [dotenv](https://github.com/theskumar/python-dotenv) to load API tokens, passwords, connection 
strings, and other configuration settings from environment variables and .env files. You then pass your security 
information as variables when you interact with your database.

1. In your Python environment, include the dotenv packages:

    ```bash
    pip install python-dotenv
    pip install psycopg2-binary
    ```
    TODO: could we not install these packages with the install scripts?

1. Set your OpenAI key as an environment variable:
    ```bash
    OPENAI_AI_KEY="this-is-my-super-secret-api-key-dont-tell"
    DB_URL="your connection string"
    ```

1. Pass your API key as a parameter to your queries:

    ```python
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    DB_URL = os.environ["DB_URL"]
    
    import psycopg2
    
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            # pass the API key as a parameter to the query. don't use string manipulations
            cur.execute("SELECT * FROM openai_list_models(%s) ORDER BY created DESC", (OPENAI_API_KEY,))
            records = cur.fetchall()
    ```

    Do not use string manipulation to embed the key as a literal in the SQL query.

## Usage

- [open_ai_list_models](#open_ai_list_models): list the models supported by OpenAI functions in pgai.
- [openai_tokenize](#openai_tokenize): encode content into tokens. 
- [openai_detokenize](#openai_detokenize): turn tokens into natural language.
- [openai_embed](#openai_embed): generate [embeddings](https://platform.openai.com/docs/guides/embeddings) using a 
  specified model.
- [openai_chat_complete](#openai_chat_complete): generate text or complete a chat using key words and phrases.
- [openai_moderate](#openai_moderate): check if content is classified as potentially harmful:


### open_ai_list_models

List the models supported by OpenAI functions in pgai.

```sql
SELECT * 
FROM openai_list_models($1)
ORDER BY created DESC
\bind :OPENAI_API_KEY
\g
```
The data returned looks like:

```text
             id              |        created         |    owned_by     
-----------------------------+------------------------+-----------------
 gpt-4o-test-shared          | 2024-05-20 13:06:56-05 | system
 gpt-4o-2024-05-13           | 2024-05-10 14:08:52-05 | system
 gpt-4o                      | 2024-05-10 13:50:49-05 | system
 gpt-4-turbo-2024-04-09      | 2024-04-08 13:41:17-05 | system
 gpt-4-turbo                 | 2024-04-05 18:57:21-05 | system
 ...
(N rows)
```

### openai_tokenize

To encode content and count the number of tokens returned:

* Encode content into an array of tokens.

    ```sql
    SELECT openai_tokenize
    ( 'text-embedding-ada-002'
    , 'Timescale is Postgres made Powerful'
    );
    ```
    The data returned looks like:
    ```text
                openai_tokenize             
    ----------------------------------------
     {19422,2296,374,3962,18297,1903,75458}
    (1 row)
    ```

* Count the number of tokens generated:

    ```sql
    SELECT array_length
    ( openai_tokenize
      ( 'text-embedding-ada-002'
      , 'Timescale is Postgres made Powerful'
      )
    , 1
    );
    ```
    The data returned looks like:
    ```text
     array_length 
    --------------
                7
    (1 row)
    ```

### openai_detokenize

Turn tokenized content into natural language:

```sql
SELECT openai_detokenize('text-embedding-ada-002', array[1820,25977,46840,23874,389,264,2579,58466]);
```
The data returned looks like:

```text
             openai_detokenize              
--------------------------------------------
 the purple elephant sits on a red mushroom
(1 row)
```

### openai_embed

Generate [embeddings](https://platform.openai.com/docs/guides/embeddings) using a specified model.

- Request an embedding using a specific model.

    ```sql
    SELECT openai_embed
    ( $1
    , 'text-embedding-ada-002'
    , 'the purple elephant sits on a red mushroom'
    )
    \bind :OPENAI_API_KEY
    \g
    ```

    The data returned looks like:
    
    ```text
                          openai_embed                      
    --------------------------------------------------------
     [0.005978798,-0.020522336,...-0.0022857306,-0.023699166]
    (1 row)
    ```

- Specify the number of dimensions you want in the returned embedding:

    ```sql
    SELECT openai_embed
    ( $1
    , 'text-embedding-ada-002'
    , 'the purple elephant sits on a red mushroom'
    , _dimensions=>768
    )
    \bind :OPENAI_API_KEY
    \g
    ```
    This only works for certain models.

- Pass a user identifier.

    ```sql
    SELECT openai_embed
    ( $1
    , 'text-embedding-ada-002'
    , 'the purple elephant sits on a red mushroom'
    , _user=>'bac1aaf7-4460-42d3-bba5-2957b057f4a5'
    )
    \bind :OPENAI_API_KEY
    \g
    ```

- Pass an array of text inputs.

    ```sql
    SELECT openai_embed
    ( $1
    , 'text-embedding-ada-002'
    , array['Timescale is Postgres made Powerful', 'the purple elephant sits on a red mushroom']
    )
    \bind :OPENAI_API_KEY
    \g
    ```

- Provide tokenized input.

    ```sql
    select openai_embed
    ( $1
    , 'text-embedding-ada-002'
    , array[1820,25977,46840,23874,389,264,2579,58466]
    )
    \bind :OPENAI_API_KEY
    \g
    ```

### openai_chat_complete

Generate text or complete a chat using key words and phrases:

* Return different possible answers for a specific question from a specific persona:

    ```sql
    \pset tuples_only on
    \pset format unaligned
    
    SELECT jsonb_pretty
    (
      openai_chat_complete
      ( $1
      , 'gpt-4o'
      , jsonb_build_array
        ( jsonb_build_object('role', 'system', 'content', 'you are a helpful assistant')
        , jsonb_build_object('role', 'user', 'content', 'what is the typical weather like in Alabama in June')
        )
      )
    )
    \bind :OPENAI_API_KEY
    \g
    ```
  The data returned looks like:
    ```json
    {
        "id": "chatcmpl-9RgehyQ0aydAkQajrN6Oe0lepERKC",
        "model": "gpt-4o-2024-05-13",
        "usage": {
            "total_tokens": 332,
            "prompt_tokens": 26,
            "completion_tokens": 306
        },
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "In Alabama, June typically ushers in the summer season with warm to hot temperatures and relatively high humidity. Here’s a general overview of what you can expect:\n\n1. **Temperature**: \n   - Average daytime highs usually range from the mid-80s to low 90s Fahrenheit (around 29-35°C).\n   - Nighttime temperatures often fall to the mid-60s to mid-70s Fahrenheit (18-24°C).\n\n2. **Humidity**:\n   - Humidity levels can be quite high, making the temperatures feel even warmer. The mix of heat and humidity can lead to a muggy atmosphere.\n\n3. **Rainfall**:\n   - June is part of the wet season for Alabama, so you can expect a fair amount of rainfall. Thunderstorms are relatively common, often in the afternoons and evenings.\n   - The precipitation can be sporadic, with sudden downpours that can clear up quickly.\n\n4. **Sunshine**:\n   - There are plenty of sunny days, though the sunshine can be intense. Ultraviolet (UV) levels are high, so sun protection is important.\n\n5. **Overall Climate**:\n   - Generally, the climate in Alabama in June is characterized by a typical Southeastern U.S. summer: hot, humid, and occasionally stormy. \n\nIf you’re planning a visit or activities in Alabama during June, it’s a good idea to stay hydrated, wear light clothing, and keep an eye on the weather forecast for any potential thunderstorms."
                },
                "logprobs": null,
                "finish_reason": "stop"
            }
        ],
        "created": 1716385851,
        "system_fingerprint": "fp_729ea513f7"
    }
    ```

- Return the content as text from a specific message in the choices array.

    `openai_chat_complete` returns a [jsonb object](https://www.depesz.com/2014/03/25/waiting-for-9-4-introduce-jsonb-a-structured-format-for-storing-json/) containing the
    response from the API. Use jsonb operators and functions to manipulate the object returned. For example, the 
    following query returns the content as text from the first message in the choices array.
    
    ```sql
    \pset tuples_only on
    \pset format unaligned
    
    select openai_chat_complete
    ( 'gpt-4o'
    , :'OPENAI_API_KEY'
    , jsonb_build_array
      ( jsonb_build_object('role', 'system', 'content', 'you are a helpful assistant')
      , jsonb_build_object('role', 'user', 'content', 'what is the typical weather like in Alabama in June')
      )
    )->'choices'->0->'message'->>'content'
    ;
    ```
    The data returned looks like:

    ```text
    In June, Alabama generally experiences warm to hot weather as it transitions into summer. Typical conditions include:
    
    1. **Temperatures**: Daytime highs usually range from the mid-80s to low 90s Fahrenheit (around 29-34°C). Nighttime lows typically range from the mid-60s to low 70s Fahrenheit (around 18-23°C).
    
    2. **Humidity**: June tends to be quite humid, which can make the temperatures feel even warmer. High humidity levels are characteristic of Alabama summers.
    
    3. **Precipitation**: June is part of the wetter season in Alabama, with regular afternoon thunderstorms being common. Rainfall can vary, but you can expect an average of about 4 to 5 inches (around 100-125 mm) of rain for the month.
    
    4. **Sunshine**: There are usually plenty of sunny days, although the frequent thunderstorms can lead to overcast skies at times.
    
    Overall, if you're planning to visit Alabama in June, be prepared for hot and humid conditions, and keep an umbrella or rain jacket handy for those afternoon storms.
    ```

### openai_moderate

Check if content is classified as potentially harmful:

```sql
\pset tuples_only on
\pset format unaligned

select jsonb_pretty
(
  openai_moderate
  ( $1
  , 'text-moderation-stable'
  , 'I want to kill them.'
  )
)
\bind :OPENAI_API_KEY
\g
```
The data returned looks like:

```text
{
    "id": "modr-9RsN6qZWoZYm1AK4mtrKuEjfOcMWp",
    "model": "text-moderation-007",
    "results": [
        {
            "flagged": true,
            "categories": {
                "hate": false,
                "sexual": false,
                "violence": true,
                "self-harm": false,
                "self_harm": false,
                "harassment": true,
                "sexual/minors": false,
                "sexual_minors": false,
                "hate/threatening": false,
                "hate_threatening": false,
                "self-harm/intent": false,
                "self_harm_intent": false,
                "violence/graphic": false,
                "violence_graphic": false,
                "harassment/threatening": true,
                "harassment_threatening": true,
                "self-harm/instructions": false,
                "self_harm_instructions": false
            },
            "category_scores": {
                "hate": 0.2324090600013733,
                "sexual": 0.00001205232911161147,
                "violence": 0.997192919254303,
                "self-harm": 0.0000023696395601291442,
                "self_harm": 0.0000023696395601291442,
                "harassment": 0.5278584957122803,
                "sexual/minors": 0.00000007506431387582779,
                "sexual_minors": 0.00000007506431387582779,
                "hate/threatening": 0.024183575063943863,
                "hate_threatening": 0.024183575063943863,
                "self-harm/intent": 0.0000017161115692942985,
                "self_harm_intent": 0.0000017161115692942985,
                "violence/graphic": 0.00003399916022317484,
                "violence_graphic": 0.00003399916022317484,
                "harassment/threatening": 0.5712487697601318,
                "harassment_threatening": 0.5712487697601318,
                "self-harm/instructions": 0.000000001132860139030356,
                "self_harm_instructions": 0.000000001132860139030356
            }
        }
    ]
}
```

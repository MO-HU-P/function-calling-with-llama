# Llama-3-8B (Meta) にウェブ検索機能を実装したアプリケーション

このリポジトリには、Llama-3-8B（Meta）にfunction callingを実装したPythonファイル(`app.py`)があります。このアプリの構築には、OllamaとLangchainのOllamaFunctionsライブラリを利用しています。モデルが必要に応じてウェブ検索し、ユーザーの質問に最新の情報を踏まえて回答を提供します。また、モデルが既に持っている知識に新しい情報を加えて回答することもできます。

## 事前準備

### Ollamaのインストール

1. [Ollama](https://github.com/ollama/ollama)をインストールします。

2. ターミナルから以下のコマンドを実行し、`llama3`をダウンロードします。

```
ollama pull llama3
```

### Langchainの設定

Langchainの[OllamaFunctions](https://python.langchain.com/v0.1/docs/integrations/chat/ollama_functions/)のインスタンスをllama3で初期化します。

```python
base_model="llama3"
model = OllamaFunctions(model=base_model, format="json")
```

### ウェブ検索機能の実装

ウェブ検索のための関数をモデルにバインドして、モデルが関数を呼び出すようにしています。

```python
model = model.bind_tools(
    tools=[
        {
            "name": "get_web_search",
            "description": "Get the top k search results (title, body, url) from website for a given query. 'title' refers to the title of the webpage or the name of the website. 'body' refers to the document body or content of the webpage. 'url' refers to the uniform resource locator, which is the address of the webpage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                    "search_url_count": {
                        "type": "integer",
                        "description": "The number of searching URL to use",
                    },
                },
                "required": ["query"],
            },
        }
    ]
)
functions = {
    "get_web_search": run_web_search,
}
```

### アプリの実行

1. ターミナルから以下のコマンドを実行します。

```
python app.py
```

2. `app.py`ファイルを実行すると、main関数が呼び出され、ターミナルに[Query:  ]というメッセージが表示されます。

3. ユーザーの質問をターミナルに入力し、Enterキーを押します。

例：
```
Query: Who is the Prime Minister of Japan in 2024?
```

### 処理の流れ

1. ユーザーの質問が以下のプロンプトテンプレートに含まれ、LLMに渡されます。

```python
prompt = """To appropriately answer the user's question, it would be helpful to search for the latest web information.

User's Question: {query}

Please use the search results as a reference to provide a comprehensive answer to the question."""
```

2. モデルがウェブ検索の必要性を判断した場合、first_responseでtool_callsに'get_web_search'という'name'が含まれます。

例:
```
content='' 
    id='run-・・・・・・・・' 
    tool_calls=[{
        'name': 'get_web_search', 
        'args': {'query': 'Prime Minister of Japan 2024', 
                 'search_url_count': 5}, 
                 'id': 'call_・・・・・・・・'
                }
            ]
```

3. run_web_search()関数を実行して、DuckDuckGoを使ってユーザーのクエリに基づきウェブ検索を行います。デフォルトでは上位3件のウェブ情報を取得しますが、search_url_countの値を変更することで取得件数を調整できます。
なお、上記の例の場合では、'args'中のsearch_url_countの数値が5になっているため、上位5番目までの情報を取得するよう更新されます。

4. prompt、first_response_message、Search resultsがMessagesに代入され、再度モデルに渡されて最終的な回答が生成されます。

```python
second_response = model.invoke(messages)
```


## 必要なパッケージ

- langchain_experimental
- langchain_core
- duckduckgo_search

これらのパッケージはrequirements.txtに記載されています。


## 試行例と考察

### 試行例

入力したQueryを「Who is the Prime Minister of Japan in 2024?」とした場合、以下の回答結果が示されました。
回答例1・2は、予想される結果が得られたパターンとなります。

- 回答例1

```
### Answer: According to the latest search results, the Prime Minister of Japan in 2024 is Fumio Kishida. He took office after succeeding Yoshihide Suga and has been actively involved in various events and meetings with other world leaders.

### Search results:
Title: The Prime Minister in Action from January 2024 - japan.kantei.go.jp
URL: https://japan.kantei.go.jp/101_kishida/actions/202401/index.html
Body: Presentation of Anpogaki Persimmons by Governor of Fukushima Prefecture and Others. January 26, 2024. On January 26, 2024, Prime Minister Kishida was presented with Anpogaki persimmons from Mr. UCHIBO...
（Search resultはweb情報があと２つ表示されましたが、省略）
```

- 回答例2
```
### Answer: As of 2024, the Prime Minister of Japan is Fumio Kishida. He has been serving in this position since 2021 and has previously held various ministerial positions, including Foreign Affairs and Defense.

### Search results:
（Search resultはweb情報が５つ表示されましたが、省略）
```

以下、入力したQueryは上記と同様の回答例3～6です。回答例3は、web検索せずにLLMが独自の知識で回答しているパターンとなりますが、回答例4では、my latest web searchと答えつつも、web検索せず情報が示されていないため、すなわち回答の出力に問題のあるパターンと言えます。しかしながら、LLMは最新の情報を確認するようユーザーに促している点は慎重な回答ができていると思われます。回答例5は、web検索してweb情報は取得されていますが、最終回答（Answer）が出力されていない問題があります。回答例6については、トラブルにより、エラーが発生して完全に失敗したパターンとなります。

- 回答例3
```
### Answer: As of my knowledge cutoff, the current information available suggests that Fumio Kishida is the Prime Minister of Japan (2022-present). Please note that this information might have changed since then. For more accurate and up-to-date information, I recommend checking official government sources or reputable news outlets in 2024.
```

- 回答例4
```
### Answer: As per my latest web search, the current information available suggests that Fumio Kishida is the Prime Minister of Japan as of 2024. However, please note that the information may change over time. If you need more recent or accurate data, I recommend verifying with a reliable source.
```

- 回答例5
```
### Answer: 

### Search results:
Title: Fumio Kishida: Japan's new prime minister takes office - BBC
URL: https://www.bbc.com/news/world-asia-58784635
Body: Fumio Kishida has formally taken office as Japan's new prime minister, succeeding Yoshihide Suga who resigned after just one year in office. Mr Kishida, 64, won the race to lead Japan's ruling ...

（Search resultはweb情報があと２つ表示されましたが、省略）
```

- 回答例6
```
An error occurred: 'tool'
```

次に入力したQueryを「What is the highest mountain in Japan?」とした場合のひとつの例です。以下のような回答例7が出力されました。常識的な質問でウェブ検索しなくても回答できると思われますが、ウェブ検索しています。しかし、出力された回答は内容的に正確であり、ウェブの検索も適切に行われたと判断できます。

- 回答例7

```
### Answer: According to the latest search results, the highest mountain in Japan is indeed Mount Fuji, standing at a height of 12,388 feet (3,776 meters). It's an active stratovolcano located on Honshu Island and has been dormant since its last eruption in 1707. Additionally, it's not only the tallest mountain in Japan but also the seventh-highest peak of an island on Earth.

### Search results:
Title: Mount Fuji | Facts, Height, Location, & Eruptions | Britannica
URL: https://www.britannica.com/place/Mount-Fuji
Body: Mount Fuji, highest mountain in Japan. It rises to 12,388 feet (3,776 meters) near the Pacific coast of central Honshu, about 60 miles (100 km) west of the Tokyo-Yokohama metropolitan area. It is a vo...

（Search resultはweb情報があと２つ表示されましたが、省略）
```


### 考察

[Meta](https://llama.meta.com/llama3/)によると、Llama-3-8Bは他の類似モデルと比較して高い性能が示されています。個人の使用感においても、その回答の素晴らしさを直感的に感じることができます。一方で、上記の試行例のように、回答の生成が不安定である場合もあります。

その要因として、8Bというパラメーター数の小規模なモデルの限界があるかもしれません。しかし、主な要因としてはプロンプトの内容に大きく影響されることが考えられます。上記の説明にあるように、プロンプトはシステムプロンプトとユーザーの質問から構成されますが、システムプロンプトについてはさらに検討の余地があると思われます。

この`app.py`は、上記のコードの説明を参照していただき、Visual Studio Codeなどのコードエディタで自由にカスタマイズできます。Ollamaでサポートされている別のモデルに変更することや、モデルが扱えるtool（関数）を増やすことも可能です。ただし、本スクリプトはウェブ検索がメインになるようプログラムされているため、柔軟な変更は難しい可能性があります。





# autocom
# 📌 뉴스 상투적 표현 자동완성 시스템

## 1. 개발 환경
- **백엔드:** Python, Elasticsearch  
- **버전 및 이슈 관리:** GitHub, GitHub Issues, GitHub Projects    
- **API 문서화 및 테스트:** Postman

---

## 2. 프로젝트 
**뉴스 기사에서 자주 사용되는 상투적 표현을 자동완성**하는 **Elasticsearch 기반의 시스템**입니다.**빠르게 상투적표현을 자동완성**할 수 있도록 도와줍니다. **Elasticsearch 기반 자동완성에서 LLM(GPT-4, KoBERT 등)을 활용하여 문맥적인 적절성을 높이는 실험** 진행 예정입니다.

---

## 3. 주요 기능
✅ **빠른 자동완성 기능**  
- `edge_ngram_filter`를 활용하여 **빠른 접두(prefix) 기반 검색** 제공 (완료)

✅ **맞춤형 인덱싱**  
- **뉴스 상투적 표현 데이터셋**을 사전 구축하여 저장 및 관리 (완료)

✅ **문맥 기반 순위 조정 (추후 업데이트)**  
- GPT-4, KoBERT 등 **대규모 언어 모델(LLM)**을 활용하여 **더 적절한 표현 추천** (진행 중)

✅ **유연한 검색 지원**  
- 부분 문구 검색이 가능하며, **초기 입력값을 기준으로 유사 표현 추천**

---

## 4. 데이터 처리 방식
### 🔹 **상투적 표현 데이터셋**
- **실제 뉴스 기사에서 추출한 상투적표현 데이터** 활용  
- **기사 작성에서 자주 사용되는 문장 패턴** 저장  
- Elasticsearch 인덱스를 활용한 **빠른 검색 최적화**

### 🔹 **인덱싱 및 검색 방식**
- `news_cliche_autocomplete`라는 **Elasticsearch 인덱스**를 생성  
- `match_phrase_prefix`를 활용한 **부분 구문 검색 지원**  
- **저장 속성:** `suggest` (자동완성을 위한 문구)

---

## 5. API 명세
| **엔드포인트**              | **HTTP 메서드** | **설명**                                        |
|---------------------------|------------|--------------------------------------------|
| `/health`                 | GET        | Elasticsearch 클러스터 상태 확인              |
| `/index`                  | GET        | 현재 저장된 모든 인덱스 조회                   |
| `/delete/{index_name}`     | DELETE     | 특정 인덱스 삭제                             |
| `/create/{index_name}`     | POST       | 일반적인 인덱스 생성                         |
| `/create_auto/{index_name}`| POST       | **자동완성 기능이 포함된** 인덱스 생성          |
| `/insert_auto_file`        | POST       | 파일을 통해 상투적 표현 데이터 삽입              |
| `/autocomplete/{query}`    | GET        | 입력값을 기반으로 자동완성 문구 검색             |

---

## 6. 상세 구현 내용
### 🔹 **Elasticsearch 자동완성 인덱스 생성**
```
[
    {
        "health": "red",
        "status": "open",
        "index": ".geoip_databases",
        "uuid": "P40ucw49T6u5NrEULDyNmQ",
        "pri": "1",
        "rep": "0",
        "docs.count": null,
        "docs.deleted": null,
        "store.size": null,
        "pri.store.size": null
    },
    {
        "health": "green",
        "status": "open",
        "index": "seoul_autocom",
        "uuid": "9r5loWWaSZ6SpUzc4kR0mA",
        "pri": "1",
        "rep": "0",
        "docs.count": "50",
        "docs.deleted": "0",
        "store.size": "10.6kb",
        "pri.store.size": "10.6kb"
    },
    {
        "health": "green",
        "status": "open",
        "index": "jiho",
        "uuid": "EYzJ48t-QlGxwiG-iXnIqA",
        "pri": "1",
        "rep": "0",
        "docs.count": "1064",
        "docs.deleted": "0",
        "store.size": "170.8kb",
        "pri.store.size": "170.8kb"
    },
    {
        "health": "green",
        "status": "open",
        "index": "wiki",
        "uuid": "_4saoQ-xTyKn64O6t8o7YQ",
        "pri": "1",
        "rep": "0",
        "docs.count": "1651942",
        "docs.deleted": "0",
        "store.size": "1015.7mb",
        "pri.store.size": "1015.7mb"
    },
    {
        "health": "green",
        "status": "open",
        "index": "national",
        "uuid": "QxQfUJsvS8Suvvpy35voMQ",
        "pri": "1",
        "rep": "0",
        "docs.count": "72421",
        "docs.deleted": "0",
        "store.size": "96.3mb",
        "pri.store.size": "96.3mb"
    }
]
```

### 🔹 **데이터 삽입 (파일 기반)**
```python
def insert_autocomplete_data_from_file(self, index_name, file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            phrases = [line.strip() for line in file.readlines() if line.strip()]
            for i, phrase in enumerate(phrases):
                doc = {"suggest": phrase.lower()}  # 소문자로 변환하여 저장
                res = self.es.index(index=index_name, id=i + 1, document=doc)
                assert res['result'] == "created", f"{phrase} 삽입 실패"
        print("자동 완성 데이터 삽입 완료!")
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
    except Exception as e:
        print(f"오류 발생: {str(e)}")
```

### 🔹 **자동완성 검색**
```python
def autocomplete(self, index_name, query):
    body = {
        "query": {
            "prefix": {
                "suggest": query.lower()  # 소문자로 변환 후 검색
            }
        }
    }
    res = self.es.search(index=index_name, body=body)
    suggestions = res['hits']['hits']
    return [suggestion['_source']['suggest'] for suggestion in suggestions]
```

---

## 7. 사용 방법
### 📌 **클러스터 상태 확인**
```bash
python autocomplete_manager.py health
```

### 📌 **모든 인덱스 조회**
```bash
python autocomplete_manager.py index
```

### 📌 **기존 인덱스 삭제**
```bash
python autocomplete_manager.py delete jiho
```

### 📌 **자동완성 인덱스 생성**
```bash
python autocomplete_manager.py create_auto jiho
```

### 📌 **자동완성 데이터 삽입 (파일 기반)**
```bash
python autocomplete_manager.py insert_auto_file jiho data/cliche_list.txt
```

### 📌 **자동완성 검색 실행**
```bash
python autocomplete_manager.py autocomplete jiho "될 것으로"
```

---



## 7. 진행 중인 상황
🔹 **명령행 인자(sys.argv)에서 띄어쓰기가 포함된 경우 자동완성 기능이 정상적으로 작동하지 않는 문제 발견 → 코드 수정 중**
-----> 명령행 인자의 오류가 아닌 검색 쿼리와 데이터 인덱싱 시 분석기의 차이 때문에 발생하는 오류로 파악되어 코드 수정 중(25.02.13)
-----> **해결완료(25.02.14)**

🔹 **기존 Elasticsearch 기반 자동완성에서 LLM(GPT-4, KoBERT 등)을 활용하여 문맥적인 적절성을 높이는 실험 진행 예정**
-----> **진행 중(24.02.14)**
-----> **GPT-4 기반 재정렬/후처리(GPT-4 API 사용)** **진행완료(25.02.18)**


🔹 **RAG(Retrieval-Augmented Generation) 방식을 적용하여 검색 + LLM 자동완성을 결합하여 성능 비교 실험 진행 예정**


## 8. 관련 논문 읽기
🔗 [Elasticsearch for Autocomplete and Search](https://arxiv.org/abs/2005.11401)  
🔗 [RAG 시스템 성능 향상을 위한 웹문서 본문 정제 및 추출 시스템](file:///Users/jiho/Downloads/RAG%20%EC%8B%9C%EC%8A%A4%ED%85%9C%20%EC%84%B1%EB%8A%A5%20%ED%96%A5%EC%83%81%EC%9D%84%20%EC%9C%84%ED%95%9C%20%EC%9B%B9%EB%AC%B8%EC%84%9C%20%EB%B3%B8%EB%AC%B8%20%EC%A0%95%EC%A0%9C%20%EB%B0%8F%20%EC%B6%94%EC%B6%9C%20%EC%8B%9C%EC%8A%A4%ED%85%9C.pdf)  
🔗 [LLM + RAG 적용 개요](https://dreambind.com/llm-rag-%EB%9E%80-%EC%9E%90%EC%97%B0%EC%96%B4-%EC%B2%98%EB%A6%AC%EC%9D%98-%EC%83%88%EB%A1%9C%EC%9A%B4-%ED%8C%A8%EB%9F%AC%EB%8B%A4%EC%9E%84-%EC%B4%9D-%EC%A0%95%EB%A6%AC/?utm_source=chatgpt.com)  
🔗 [ChatGPT + Elasticsearch 적용 사례](https://www.elastic.co/search-labs/blog/chatgpt-elasticsearch-openai-meets-private-data)  
🔗 [KCI 논문: 뉴스 자동완성 개선 연구](file:///Users/jiho/Downloads/KCI_FI002772328.pdf)  
🔗 [Elasticsearch의 다국어 검색 최적화 연구](file:///Users/jiho/Improving%20Elasticsearch%20for%20Chinese,%20Japanese,%20and.pdf)  

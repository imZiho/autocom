import openai
import os
import sys
import json
import pprint as ppr
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

if openai.api_key is None:
    raise ValueError("ERROR: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
# -------------------------------------------------------------------
# GPT-4 API 호출 함수
def call_gpt4_api(prompt, model="gpt-4", max_tokens=400, temperature=0.7):
    """
    GPT-4 API를 호출하여 프롬프트에 대한 응답을 반환하는 함수입니다.
    max_tokens 값을 400으로 늘려 긴 응답을 생성할 수 있도록 합니다.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"GPT-4 API 호출 중 오류 발생: {e}")
        return None

# -------------------------------------------------------------------
# 후보 재정렬 함수 (GPT-4 후처리)
def re_rank_candidates(user_query, candidates):
    """
    사용자 쿼리와 후보 목록을 기반으로 GPT-4에게 문맥적 적절성을 평가하고
    후보들을 순위별로 재정렬하도록 요청하는 함수입니다.
    프롬프트에 '완전한 문장'으로 작성해 달라는 지시를 추가하여,
    전체 문장이 출력되도록 유도합니다.
    """
    prompt = (
        f"사용자가 '{user_query}'라고 입력했습니다.\n"
        "아래 추천 후보들 중에서 문맥상 가장 적절한 추천을 순위별로 나열하고, "
        "각 추천에 대해 간단한 이유를 완전한 문장으로 덧붙여 주세요.\n\n"
    )
    
    for i, candidate in enumerate(candidates, start=1):
        prompt += f"{i}. {candidate}\n"
    
    prompt += "\n결과를 순위와 함께 출력해 주세요. 답변은 전체 문장으로 작성해 주세요."
    
    llm_response = call_gpt4_api(prompt)
    return llm_response

# -------------------------------------------------------------------
# Elasticsearch 자동완성 검색 클래스
class ElasticSearch:
    def __init__(self):
        """
        Elasticsearch 클라이언트를 생성합니다.
        호스트, 타임아웃, 포트 등의 설정을 포함합니다.
        """
        self.es = Elasticsearch(hosts="localhost", timeout=1000, port=4312)

    def check_health(self):
        health = self.es.cluster.health()
        ppr.pprint(health, indent=4)

    def all_index(self):
        indices = self.es.cat.indices(format='json', pretty=True)
        print(json.dumps(indices, indent=4))

    def delete_index(self, index_name=None):
        self.es.indices.delete(index=index_name)

    def create_index(self, index_name=None):
        self.es.indices.create(
            index=index_name,
            body={
                "settings": {
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "context": {"type": "text"},
                        "author": {"type": "text"},
                        "publish": {"type": "text"},
                        "date": {"type": "text"}
                    }
                }
            }
        )

    def create_autocomplete_index(self, index_name):
        self.es.indices.create(
            index=index_name,
            body={
                "settings": {
                    "analysis": {
                        "filter": {
                            "edge_ngram_filter": {
                                "type": "edge_ngram",
                                "min_gram": 1,
                                "max_gram": 20
                            }
                        },
                        "analyzer": {
                            "autocomplete_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "edge_ngram_filter"]
                            }
                        }
                    },
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "suggest": {
                            "type": "text",
                            "analyzer": "autocomplete_analyzer"
                        }
                    }
                }
            }
        )
        print(f"자동 완성 인덱스 '{index_name}' 생성 완료!")

    def insert_autocomplete_data_from_file(self, index_name, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                phrases = [line.strip() for line in file.readlines() if line.strip()]
                for i, phrase in enumerate(phrases):
                    doc = {"suggest": phrase.lower()}  # 소문자 변환하여 삽입
                    res = self.es.index(index=index_name, id=i + 1, document=doc)
                    assert res['result'] == "created", f"{phrase} 삽입 실패"
            print("자동 완성 데이터 삽입 완료!")
        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {file_path}")
        except Exception as e:
            print(f"오류 발생: {str(e)}")

    def autocomplete(self, index_name, query):
        """
        지정한 인덱스에서 'match_phrase_prefix' 쿼리를 사용하여 자동완성 후보들을 검색합니다.
        """
        body = {
            "query": {
                "match_phrase_prefix": {
                    "suggest": query.lower()
                }
            }
        }
        res = self.es.search(index=index_name, body=body)
        suggestions = res['hits']['hits']
        return [suggestion['_source']['suggest'] for suggestion in suggestions]

# -------------------------------------------------------------------
# 메인 실행 부분: Elasticsearch 검색 및 GPT-4 후처리 결과를 함께 출력
if __name__ == "__main__":
    args = sys.argv
    es = ElasticSearch()

    # 인수로 명령어 전달시 예: python autocomplete_manager.py autocomplete jiho "될 것으로"
    if args[1] == 'health':
        es.check_health()
    elif args[1] == 'index':
        es.all_index()
    elif args[1] == 'delete':
        es.delete_index(index_name=args[2])
    elif args[1] == 'create':
        es.create_index(index_name=args[2])
    elif args[1] == 'create_auto':
        es.create_autocomplete_index(index_name=args[2])
    elif args[1] == 'insert_auto_file':
        es.insert_autocomplete_data_from_file(index_name=args[2], file_path=args[3])
    elif args[1] == 'autocomplete':
        # Elasticsearch 자동완성 검색 실행
        user_query = args[3]  # 예: "될 것으로"
        index_name = args[2]  # 예: "jiho"
        candidates = es.autocomplete(index_name, user_query)
        
        # 후보가 없으면 기본 후보 사용
        if not candidates:
            print("Elasticsearch에서 후보를 찾지 못했습니다. 기본 후보를 사용합니다.")
            candidates = [
                "될 것으로 전망된다.",
                "할 것으로 예상된다.",
                "할 수 있을까.",
                "수 있다."
            ]
        
        # Elasticsearch 결과 출력
        print("Elasticsearch 자동완성 결과:")
        for candidate in candidates:
            print(candidate)
        
        # GPT-4를 이용한 후처리(재정렬) 실행
        ranking = re_rank_candidates(user_query, candidates)
        print("\nGPT-4 재정렬 결과:")
        print(ranking)

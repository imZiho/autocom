import os
import sys
import json
import pprint as ppr
from argparse import ArgumentParser

from tqdm import tqdm
from elasticsearch import Elasticsearch

SPECIAL_CHAR = ['(', ')', '{', '}', '[', ']', '^', '~', '/', ':', '?', '!']
SPECIAL_CHAR2 = ["'", '"']


class ElasticSearch:
    def __init__(self):
        self.es = Elasticsearch(hosts="localhost", timeout=1000, port=4312)

    # 클러스터 상태 확인
    def check_health(self):
        health = self.es.cluster.health()
        ppr.pprint(health, indent=4)

    # 인덱스 목록 조회
    def all_index(self):
        indices = self.es.cat.indices(format='json', pretty=True)
        print(json.dumps(indices, indent=4))

    # 인덱스 삭제
    def delete_index(self, index_name=None):
        self.es.indices.delete(index=index_name)

    # 일반 인덱스 생성
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

    # 자동 완성 인덱스 생성
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

    # 자동 완성 데이터 삽입 (파일 기반)
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

    # 자동 완성 검색
    def autocomplete(self, index_name, query):
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



if __name__ == '__main__':
    args = sys.argv
    es = ElasticSearch()

    # 클러스터 상태 확인
    if args[1] == 'health':
        es.check_health()

    # 인덱스 조회
    elif args[1] == 'index':
        es.all_index()

    # 인덱스 삭제
    elif args[1] == 'delete':
        es.delete_index(index_name=args[2])

    # 일반 인덱스 생성
    elif args[1] == 'create':
        es.create_index(index_name=args[2])

    # 자동 완성 인덱스 생성
    elif args[1] == 'create_auto':
        es.create_autocomplete_index(index_name=args[2])

    # 자동 완성 데이터 삽입 (파일 기반)
    elif args[1] == 'insert_auto_file':
        es.insert_autocomplete_data_from_file(index_name=args[2], file_path=args[3])

    # 자동 완성 검색
    elif args[1] == 'autocomplete':
        result = es.autocomplete(index_name=args[2], query=args[3])
        print(f"추천 결과: {result}")
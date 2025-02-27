def rag_autocomplete(user_query, retrieval_func, generation_func):
    # Step 1: 검색 단계 - retrieval_func은 사용자의 쿼리에 대해 관련 문서/후보 리스트를 반환
    retrieved_candidates = retrieval_func(user_query)
    
    # Step 2: 프롬프트 구성 - 검색 결과를 포함한 프롬프트 생성
    prompt = f"사용자가 '{user_query}'라고 입력했습니다.\n"
    prompt += "다음은 검색된 관련 문서들입니다:\n"
    for i, doc in enumerate(retrieved_candidates, start=1):
        prompt += f"{i}. {doc}\n"
    prompt += "이 정보를 바탕으로, 문맥상 가장 적절한 자동완성 추천을 순위별로 나열하고, 각 추천에 대해 간단한 이유를 전체 문장으로 설명해 주세요."
    
    # Step 3: 생성 단계 - generation_func (예: GPT-4 호출) 사용하여 최종 결과 생성
    final_output = generation_func(prompt)
    return final_output

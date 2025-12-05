from src.llms.llm import get_llm_by_type
from src.prompts.template import get_prompt_template




if __name__ == '__main__':
    llm = get_llm_by_type("basic")
    message = [
        {
            "role": "system",
            "content": get_prompt_template("topic_clarification")
        },
        {
        "role": "user",
        "content": "我需要设计一个电商网站"
    }]
    response = llm.invoke(message)
    print(response.content)



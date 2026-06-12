import re
from openai import OpenAI

def _simple_text_formatting(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"[\1]", text)                  # **bold** → [bold]
    text = re.sub(r"^-{3,}\s*$", "\n", text, flags=re.MULTILINE)    # line of 3+ dashes → empty line
    text = re.sub(r"(\n\s*){3,}", "\n\n", text)                     # 3+ empty/whitespace lines → 1 empty line
    return text.strip()

def LLM_request(code):
    company_name = df_krx.loc[code, "Name"]

    content_command = (
        f"{company_name}({code}) is a listed company in Korea. Provide a detailed and specific explanation of "
        "(1) what this company's core business is, "
        "(2) why the company has shown strong performance in recent quarters, and "
        "(3) what the top 3 key issues the company is currently facing. "
    )

    format_command = (
        "Answer in Korean using plain text. "
        "Avoid vague or high-level generalizations. "
        "The total length must not exceed 700 words. "
    )

    issues, prev_response, date_prev = get_prev_response_and_issues(code)

    # if the prev gpt response is saved within 7 days, pass
    if datetime.today() - datetime.strptime(date_prev, '%Y-%m-%d') < timedelta(days=7):
        if prev_response:
            return prev_response

    if issues:
        issues_command = (
            "The following is additional information. "
            "Cross-check its validity and use it only if it is important and accurate.\n"
        )
        issues = issues_command + issues

    if prev_response:
        prev_command = (
            f"The following is your previous response to the identical query about the company on {date_prev}. "
            "Refer to it, but update your answer with any new developments since then.\n"
        )
        prev_info = prev_command + prev_response
    
    extras = "\n\n".join(filter(None, [issues, prev_info]))
    prompt = f"{content_command}\n{format_command}\n\n{extras}"

    client = OpenAI(
        api_key= "dummy", 
        base_url="http://localhost:11434/v1", # ollama
        # base_url = "https://api.perplexity.ai" # perplexity API may contain reference info, separately
    )

    # ----------------------------------
    # decommand the following to use LLM
    # ----------------------------------
    # chat_completion = client.chat.completions.create(
    #     model="gemma4", 
    #     # model="sonar-pro", # perplexity
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": (
    #                 prompt
    #             )
    #         }
    #     ],
    # )
    
    # response = chat_completion.choices[0].message.content
    # response = _simple_text_formatting(response)
    # save_LLM_response(code, response)

    # ----------------------------------
    # remove the following to enable LLM
    # ----------------------------------
    response = prev_response

    return response
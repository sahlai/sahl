import os
import sys
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.runnables import RunnableParallel
from langchain.memory import ConversationBufferMemory
from database import (get_active_prompt, get_service_providers, start_chat_session,
                      end_chat_session, add_chat_detail, get_model_settings)

# Load environment variables
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

# Initialize ChatAnthropic
llm = ChatAnthropic(anthropic_api_key=api_key, model="claude-3-sonnet-20240229")

# Define your prompt template
prompt = ChatPromptTemplate.from_template("Your prompt template here")

# Create the chain
chain = prompt | llm

# Memory setup
memory = ConversationBufferMemory(memory_key="chat_history", input_key="human_input")

# Example of RunnableParallel (you can adjust or remove if not needed)
runnable = RunnableParallel(
    passed=RunnablePassthrough(),
    modified=lambda x: x["num"] + 1,
)

# Example invocation (you can adjust or remove if not needed)
# runnable.invoke({"num": 1})

# Rest of your code...
api_key = os.getenv("ANTHROPIC_API_KEY")
claude = ChatAnthropic(anthropic_api_key=api_key, model="claude-3-sonnet-20240229")
memory = ConversationBufferMemory(memory_key="chat_history", input_key="human_input")

def get_prompt_template():
    prompt_text = get_active_prompt()
    if not prompt_text:
        print("No active prompt found, using default", file=sys.stderr)
        prompt_text = """
        أنت مساعد ذكي لشركة SAHL، متخصص في ربط المستخدمين بمقدمي الخدمات. اتبع هذه التعليمات بدقة:
        1. استخدم فقط المعلومات المتوفرة في {context}. لا تختلق أي معلومات إضافية.
        2. عند طلب خدمة، استجب بالصيغة التالية بالضبط:
           سعيد بمساعدتك. طلبت [الخدمة] في [المدينة]. 
           [إذا توفرت معلومات في {context}]:
           لدينا مقدمي الخدمة التاليين:
           [اسم] - [خدمات] - [مدن] - [هاتف]
           [كرر لكل مقدم خدمة متوفر]
           [إذا لم تتوفر معلومات]:
           عذرًا، لا تتوفر حاليًا معلومات عن [الخدمة] في [المدينة].
        3. كن مختصراً في ردودك. تجنب الإطالة أو إضافة معلومات غير ضرورية.
        4. إذا لم تتوفر معلومات محددة في {context}، لا تقدم أي افتراضات أو تخمينات.
        5. إذا كان السؤال غير مباشر أو غامض، اطلب توضيحاً قبل تقديم معلومات.
        6. اختم كل رد بسؤال مفتوح مثل "هل هناك شيء آخر يمكنني مساعدتك به؟"
        تاريخ المحادثة: {chat_history}
        سؤال العميل: {human_input}
        المعلومات المتاحة: {context}
        المساعد:
        """
    return ChatPromptTemplate.from_template(prompt_text)

prompt = get_prompt_template()

# Using LLMChain
conversation_chain = LLMChain(
    llm=claude,
    prompt=prompt,
    memory=memory
)

# Keep RunnablePassthrough as an alternative (commented out for now)
# conversation_chain = (
#     RunnablePassthrough.assign(chat_history=memory.load_memory_variables)
#     | prompt
#     | claude
# )

def estimate_tokens(text):
    # تقدير بسيط: افتراض أن كل كلمة هي رمز مميز واحد
    return len(text.split())

def process_user_input(user_input, session_id=None):
    try:
        providers = get_service_providers()
        context = "مقدمو الخدمات المتاحون:\n"
        for provider in providers:
            context += f"- {provider['name']}: {provider['services']} في {provider['cities']}. هاتف: {provider['phone']}\n"
            if provider['service_details']:
                context += f"  تفاصيل الخدمة: {provider['service_details']}\n"

        input_tokens = estimate_tokens(user_input + context)

        # Using LLMChain
        response = conversation_chain.predict(human_input=user_input, context=context)

        # If using RunnablePassthrough (commented out for now)
        # response = conversation_chain.invoke({
        #     "human_input": user_input,
        #     "context": context
        # })

        output_tokens = estimate_tokens(response)

        if session_id:
            add_chat_detail(session_id, user_input, response, input_tokens, output_tokens)

        print(f"Response generated: {response[:100]}...", file=sys.stderr)  # Print first 100 chars of response for debugging
        return response, input_tokens, output_tokens
    except Exception as e:
        print(f"Error in process_user_input: {str(e)}", file=sys.stderr)
        return "عذرًا، حدث خطأ أثناء معالجة طلبك. الرجاء المحاولة مرة أخرى.", 0, 0

def update_prompt():
    global prompt, conversation_chain
    new_prompt = get_prompt_template()
    if new_prompt:
        prompt = new_prompt
        conversation_chain = LLMChain(llm=claude, prompt=prompt, memory=memory)
        print("Prompt updated and applied to chatbot", file=sys.stderr)
    else:
        print("Failed to update prompt, using existing one", file=sys.stderr)

def start_new_chat_session(requested_service, location):
    return start_chat_session(requested_service, location)

def end_current_chat_session(session_id):
    end_chat_session(session_id, [])  # Assuming no recommended providers for now

def get_chat_cost(input_tokens, output_tokens):
    model_settings = get_model_settings()
    if model_settings:
        input_cost = input_tokens * model_settings[2]  # input_token_price
        output_cost = output_tokens * model_settings[3]  # output_token_price
        return input_cost + output_cost
    return 0
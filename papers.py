import requests
from xml.etree import ElementTree
import pandas as pd
from transformers import MarianMTModel, MarianTokenizer, BartForConditionalGeneration, BartTokenizer
import torch
from concurrent.futures import ThreadPoolExecutor, as_completed

# 指定使用的设备
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# print(f"Using device: {device}")
def process_entry(entry, translate_model, translate_tokenizer, summarize_model, summarize_tokenizer):
    """处理单个条目的翻译和总结任务"""
    title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
    abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
    summarized_abstract = summarize_text(abstract, summarize_model, summarize_tokenizer)
    translated_abstract = translate_text(abstract, translate_model, translate_tokenizer, "zh")
    translated_summary = translate_text(summarized_abstract, translate_model, translate_tokenizer, "zh")
    return [title, abstract, translated_abstract, summarized_abstract, translated_summary]
# 加载翻译模型
translate_model_path = "H:/Paper_model/Translate"
translate_tokenizer = MarianTokenizer.from_pretrained(translate_model_path)
translate_model = MarianMTModel.from_pretrained(translate_model_path).to(device)

# 加载总结模型
summarize_model_path = "H:/Paper_model/Summarizer"
summarize_tokenizer = BartTokenizer.from_pretrained(summarize_model_path)
summarize_model = BartForConditionalGeneration.from_pretrained(summarize_model_path).to(device)

def translate_text(text, model, tokenizer, target_language="zh"):
    try:

        # 使用更新的方法调用tokenizer
        inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True, padding="max_length").to(device)
        outputs = model.generate(inputs['input_ids'], max_length=512)
        translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return translated_text
    except Exception as e:
        print(f"Translation failed: {e}")
        return "Translation failed."


def summarize_text(text, model, tokenizer):
    try:

        inputs = tokenizer(text, return_tensors="pt", padding="max_length", truncation=True, max_length=512).to(device)
        outputs = model.generate(**inputs, max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return summary
    except Exception as e:
        print(f"Summarization failed: {e}")
        return "Summarization failed."

def get_query_string(items, operation="OR"):
    if operation.upper() == "AND":
        return '+AND+'.join(f'all:{item}' for item in items)
    else:
        return '+OR+'.join(f'all:{item}' for item in items)

def search_arxiv(keywords, categories, max_results=10, sort_choice='3', operation="OR"):
    sort_options = {
        '1': ('lastUpdatedDate', 'descending'),
        '2': ('lastUpdatedDate', 'ascending'),
        '3': ('submittedDate', 'descending'),
        '4': ('submittedDate', 'ascending'),
        '5': ('relevance', 'ascending')
    }
    sort_by, sort_order = sort_options.get(sort_choice, ('submittedDate', 'descending'))
    categories_query = get_query_string(categories, operation)
    search_query = get_query_string(keywords.split(','), operation)
    url = f"http://export.arxiv.org/api/query?search_query=({search_query})+AND+({categories_query})&sortBy={sort_by}&sortOrder={sort_order}&start=0&max_results={max_results}"
    response = requests.get(url)
    if response.status_code != 200:
        print("请求失败, 状态码:", response.status_code)
        return

    try:
        root = ElementTree.fromstring(response.content)
        entries = root.findall('{http://www.w3.org/2005/Atom}entry')
        if not entries:
            print("没有找到相关文献。")
            return

        # 使用 ThreadPoolExecutor 来加速翻译和总结任务
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_entry, entry, translate_model, translate_tokenizer, summarize_model,
                                       summarize_tokenizer) for entry in entries]
            data = [future.result() for future in as_completed(futures)]

        # 保存到Excel
        df = pd.DataFrame(data, columns=['Title', 'Abstract', 'Translated Abstract', 'Summarized Abstract',
                                         'Translated Summary'])
        df.to_excel(f"{keywords.replace(' ', '_')}.xlsx", index=False)
    except ElementTree.ParseError:
        print("解析XML时发生错误。请检查API响应格式。")

if __name__ == "__main__":
    # 使用示例
    keywords = input("请输入搜索关键词：")
    operation_keywords = input("选择关键词连接方式（AND/OR）：")
    categories_input = input("请输入想要搜索的分类（例如 cs.AI,cs.LG），用逗号分隔：")
    operation_categories = input("选择分类连接方式（AND/OR）：")
    categories = categories_input.split(',')
    max_results = input("请输入最大结果数：")
    print("请选择排序选项：\n1. Announcement Date (newest first)\n2. Announcement Date (oldest first)\n3. Submission Date (newest first)\n4. Submission Date (oldest first)\n5. Relevance")
    sort_choice = input()
    search_arxiv(keywords, categories, int(max_results), sort_choice, operation_keywords)

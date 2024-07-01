import PySimpleGUI as sg
import threading
from new_papers import search_arxiv  # 确保正确导入search_arxiv函数
import warnings


# 忽略特定类型的PyTorch警告
warnings.filterwarnings("ignore", category=UserWarning, message=".*TypedStorage is deprecated.*")

def threaded_search(window, keywords, categories, max_results, sort_choice, keywords_op, categories_op):
    output = search_arxiv(keywords, categories, max_results, sort_choice, keywords_op, categories_op)
    window.write_event_value('-THREAD-', output)

def update_input_list(input_key, listbox_key, values, window):
    # 从列表框选择更新输入框，若输入框已有内容，则追加新内容
    current = values[input_key]
    selected = ', '.join(values[listbox_key])
    if current:
        if selected:
            new_value = ', '.join([current, selected]) if current else selected
        else:
            new_value = current
    else:
        new_value = selected
    window[input_key].update(new_value)

def create_window():
    keyword_choices = ['Large Language Model', 'Natural Language Processing (NLP)',
                       'Computer Vision (CV)', 'Artificial Intelligence (AI)',
                       'Machine Learning (ML)', 'Deep Learning', 'Bioinformatics',
                       'Genomics', 'Transcriptomics', 'Neural Networks',
                       'Reinforcement Learning', 'Pattern Recognition', 'Knowledge Representation']
    category_choices = ['cs.AI', 'cs.CE', 'cs.CL', 'cs.CV', 'cs.LG']
    operation_choices = ['AND', 'OR']

    layout = [
        [sg.Text("请选择搜索关键词："), sg.InputText('', size=(25, 1), enable_events=True, key='KEYWORDS_INPUT'), sg.Listbox(keyword_choices, select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED, size=(30, 6), key='KEYWORDS_LIST', enable_events=True)],
        [sg.Text("选择关键词连接方式："), sg.Combo(operation_choices, default_value='OR', key='KEYWORDS_OP')],
        [sg.Text("请选择搜索的分类："), sg.InputText('', size=(25, 1), enable_events=True, key='CATEGORIES_INPUT'), sg.Listbox(category_choices, select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED, size=(30, 6), key='CATEGORIES_LIST', enable_events=True)],
        [sg.Text("选择分类连接方式："), sg.Combo(operation_choices, default_value='OR', key='CATEGORIES_OP')],
        [sg.Text("请输入最大结果数："), sg.InputText('10', size=(8, 1), key='MAX_RESULTS')],
        [sg.Text("请选择排序选项："), sg.Combo(['Announcement Date (newest first)', 'Announcement Date (oldest first)', 'Submission Date (newest first)', 'Submission Date (oldest first)', 'Relevance'], key='SORT_CHOICE')],
        [sg.Button('Search'), sg.Button('Exit')],
        [sg.Multiline(size=(70, 15), key='OUTPUT', disabled=False)]
    ]

    return sg.Window('ArXiv Search Tool', layout)

def main():
    window = create_window()

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        if event == 'KEYWORDS_LIST':
            update_input_list('KEYWORDS_INPUT', 'KEYWORDS_LIST', values, window)
        if event == 'CATEGORIES_LIST':
            update_input_list('CATEGORIES_INPUT', 'CATEGORIES_LIST', values, window)
        if event == 'Search':
            keywords = values['KEYWORDS_INPUT']
            keywords_op = values['KEYWORDS_OP']
            categories = values['CATEGORIES_INPUT']
            categories_op = values['CATEGORIES_OP']
            max_results = int(values['MAX_RESULTS'])
            sort_choice = values['SORT_CHOICE']
            window['OUTPUT'].update("正在搜索，请稍等...\n")
            threading.Thread(target=threaded_search, args=(window, keywords, categories, max_results, sort_choice, keywords_op, categories_op), daemon=True).start()
        elif event == '-THREAD-':
            output = values[event]
            window['OUTPUT'].update(output)

    window.close()
if __name__ == "__main__":
    main()

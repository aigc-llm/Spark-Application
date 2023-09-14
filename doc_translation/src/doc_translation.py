import gradio as gr
from spark import *
from langchain.prompts import PromptTemplate
from langchain.document_loaders import Docx2txtLoader
from docx import Document
from langchain.document_loaders import UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


def translation(source_file, source_language, target_language):
    #加载文本数据
    loader = UnstructuredWordDocumentLoader(source_file.name)
    data = loader.load()

    #对文本进行切分
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 2000, chunk_overlap=0)
    texts = text_splitter.split_documents(data)

    #初始化星火大模型
    llm = Spark(temperature=0.0)

    #翻译的提示词
    fstring_template = """你是一位很专业的翻译助手，请将用三个反引号分割的文本由{source_language}翻译成{targe_language}，文本：```{text}```"""
    prompt = PromptTemplate.from_template(fstring_template)

    document = Document()
    output_file = "after_translation.docx"

    #对切分后的文本循环调用大模型进行翻译
    for page in texts:
        prompt_format = prompt.format(source_language=source_language, 
                                  targe_language=target_language, 
                                  text=page.page_content)
        print(prompt_format)
        result = llm(prompt_format)

        document.add_paragraph(result)
        
    document.save(output_file)
    return output_file

with gr.Blocks() as demo:
    gr.Markdown("""
        <div align='center' ><font size='45'>用讯飞星火大模型实现文档翻译</font></div>
    """)
    with gr.Column():
        with gr.Row():
            source_language = gr.Dropdown(['中文', '英文'], label="源语言")
            target_language = gr.Dropdown(['中文', '英文'], label="目标语言")
        with gr.Row():
            source_file = gr.File(label="源文件")
            target_file = gr.File(label="目标文件")
        button = gr.Button("翻译")

    button.click(fn=translation, 
                 inputs=[source_file, source_language, target_language], 
                 outputs=target_file)


if __name__ == "__main__":
    demo.queue(concurrency_count=3).launch()
import streamlit as st
import requests
from bs4 import BeautifulSoup
import jieba
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
from matplotlib.font_manager import FontProperties

# 设置字体路径
font_path = 'Fonts/SimHei.ttf'
font_prop = FontProperties(fname=font_path)

# 获取网页文本内容
def fetch_text_from_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        # 查找所有的span标签
        span_tags = soup.find_all('span')
        text_list = []  # 创建一个列表来存储所有span标签的文本内容
        for span in span_tags:
            text = span.get_text()  # 提取每个span标签的文本内容
            text_list.append(text.strip())  # 将文本添加到列表中，并去除前后空格
        return " ".join(text_list)  # 返回一个包含所有span标签文本的字符串，用空格分隔
    except Exception as e:
        return str(e)

# 读取停用词
def read_stopwords(file):
    with open(file, 'r', encoding='utf-8') as f:  # 确保编码格式正确
        stopwords = set(word.strip() for word in f.readlines())
    return stopwords

# 分词和词频统计
def get_word_frequency(text, stopwords):
    words = jieba.cut(text)
    filter_words = [word for word in words if word not in stopwords and len(word) > 1]
    word_counts = Counter(filter_words)  # 统计词频
    return word_counts

# 生成并展示词云
def generate_wordcloud(word_counts):
    wordcloud = WordCloud(font_path=font_path, width=800, height=600).generate_from_frequencies(word_counts)

    # 创建一个新的图形
    plt.figure(figsize=(10, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')  # 不显示坐标轴

    # 保存到缓冲区并返回
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()  # 关闭当前图形以释放内存
    buf.seek(0)  # 将指针移动到缓冲区的开始
    return buf

# 绘制瀑布图
def plot_waterfall(data):
    labels, values = zip(*data)
    fig, ax = plt.subplots()
    ax.stackplot(labels, values)
    plt.xticks(rotation=90)
    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
        label.set_fontproperties(font_prop)
    st.pyplot(fig)

# 辅助函数：绘制带有指定字体的图形
def plot_with_font(data, plot_type):
    labels, values = zip(*data)
    fig, ax = plt.subplots()
    if plot_type == "柱状图":
        ax.bar(labels, values)
    elif plot_type == "饼图":
        patches, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%')
        for text in texts:
            text.set_fontproperties(font_prop)
        for autotext in autotexts:
            autotext.set_fontproperties(font_prop)
    elif plot_type == "条形图":
        ax.barh(labels, values)
    elif plot_type == "折线图":
        ax.plot(labels, values)
    elif plot_type == "散点图":
        ax.scatter(labels, values)
    plt.xticks(rotation=90)
    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
        label.set_fontproperties(font_prop)
    return fig

# Streamlit应用
if __name__ == "__main__":
    st.title("文章词频分析与词云展示")

    # 用户输入URL
    url = st.text_input("请输入文章URL:", "")

    if url:
        # 获取网页文本内容
        text = fetch_text_from_url(url)

        if "Error" in text:
            st.error("无法抓取该页面，请检查URL是否正确")
        else:
            st.subheader("抓取的文章内容")
            st.write(text[:1000])  # 输出前1000个字符

            # 读取停用词
            stopwords_file_path = 'stoppedwords.txt'  # 确保这个路径是正确的
            stopwords = read_stopwords(stopwords_file_path)

            # 词频统计
            word_counts = get_word_frequency(text, stopwords)
            most_common_words = word_counts.most_common(20)

            # 词频排名前20
            st.subheader("词频排名前20的词汇")
            st.write(most_common_words)

            # 图表类型筛选
            chart_type = st.sidebar.selectbox("选择图表类型",
                                              ["词云图", "柱状图", "饼图", "条形图", "折线图", "散点图", "瀑布图"])

            # 绘制不同类型的图表
            if chart_type == "词云图":
                wordcloud_buf = generate_wordcloud(word_counts)
                st.image(wordcloud_buf)
            elif chart_type in ["柱状图", "饼图", "条形图", "折线图", "散点图"]:
                data = list(most_common_words)
                fig = plot_with_font(data, chart_type)
                st.pyplot(fig)
            elif chart_type == "瀑布图":
                data = list(most_common_words)
                plot_waterfall(data)

            # 交互式词频过滤
            st.subheader("交互式词频过滤")
            min_frequency = st.slider("选择最小频率", min_value=1, max_value=max(word_counts.values()), value=1)
            filtered_words = {word: count for word, count in word_counts.items() if count >= min_frequency}
            st.write(filtered_words)

### 开始

1. 创建 python 虚拟环境，并激活。

+ conda create -n doc_translation python=3.9
+ conda activate doc_translation

2. 安装依赖。

+ pip install -r requirements.txt

3. 进入 src 文件夹，修改 config.py 文件，填入自己的 **SPARK_APPID、SPARK_API_KEY 和 SPARK_API_SECRET**。

4. 运行：python doc_translation.py，运行界面如下图所示：

![interface](./assets/interface.png)

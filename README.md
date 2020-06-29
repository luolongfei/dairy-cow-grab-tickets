### 前言
🐄 奶牛抢票。大麦网抢票工具，基于 selenium。

### 使用

#### 获取源码
```shell
$ git clone https://github.com/luolongfei/dairy-cow-grab-tickets.git dairy-cow-grab-tickets/
$ cd dairy-cow-grab-tickets/
```

#### 安装依赖包
```shell
$ pip install -r requirements.txt
```

#### 配置
```shell
# 复制配置
$ cp .env.example .env

# 根据 .env 文件中的注释，将其中对应的项目改为你自己的
$ vim .env
```

#### 抢票
```shell
$ python dairy_cow.py
```

注意：`chromedriver` 路径需要根据你本地浏览器的实际情况填写，这个玩意儿必须和你浏览器版本相对应，否则启动不了。你可以去 [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads) 下载对应的 `chromedriver` 版本，并在 `.env` 文件中指明 `chromedriver 执行文件`的路径。

### 开源协议
[MIT](https://opensource.org/licenses/mit-license.php)

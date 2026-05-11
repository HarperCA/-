"""
大模型客户端封装
支持 OpenAI / DeepSeek / 通义千问 / Ollama 等
优先从环境变量读取配置，更安全
"""
import os
import json
from typing import Optional

# 尝试加载 .env 文件（如果用户创建了的话）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class LLMClient:
    """统一的大模型调用接口"""

    MODEL_ALIASES = {
        "dspro": "deepseek-v4-pro",
        "dsflash": "deepseek-v4-flash",
        "deepseek-pro": "deepseek-v4-pro",
        "deepseek-flash": "deepseek-v4-flash",
    }

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        timeout: int = 25,
        max_tokens: int = 700,
    ):
        # 优先级: 传入参数 > 环境变量 > 默认值
        self.provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.model = self.MODEL_ALIASES.get(self.model.lower(), self.model)
        self.temperature = temperature
        self.timeout = int(os.getenv("LLM_TIMEOUT", timeout))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", max_tokens))

        if not self.api_key:
            raise ValueError(
                "未配置 API Key！请选择一种方式:\n"
                "1. 创建 .env 文件（推荐，安全）\n"
                "2. 在 config.yaml 中填写 api_key\n"
                "3. 设置系统环境变量 LLM_API_KEY"
            )

        self._init_model()

    def _init_model(self):
        """根据 provider 初始化对应的 LangChain 模型"""
        try:
            if self.provider in ("openai", "deepseek"):
                from langchain_openai import ChatOpenAI
                self.client = ChatOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url if self.base_url else None,
                    model=self.model,
                    temperature=self.temperature,
                    timeout=self.timeout,
                    max_tokens=self.max_tokens,
                )
            elif self.provider == "dashscope":
                from langchain_community.chat_models import ChatTongyi
                self.client = ChatTongyi(
                    dashscope_api_key=self.api_key,
                    model=self.model,
                    temperature=self.temperature,
                )
            elif self.provider == "ollama":
                from langchain_community.chat_models import ChatOllama
                self.client = ChatOllama(
                    model=self.model,
                    base_url=self.base_url or "http://localhost:11434",
                    temperature=self.temperature,
                )
            else:
                raise ValueError(f"不支持的模型供应商: {self.provider}")
        except ImportError as e:
            raise ImportError(
                f"缺少依赖，请安装对应包: {e}\n"
                f"OpenAI/DeepSeek: pip install langchain-openai\n"
                f"通义: pip install langchain-community dashscope\n"
                f"Ollama: pip install langchain-community"
            )

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """单次对话调用"""
        messages = [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
        response = self.client.invoke(messages)
        return response.content

    def analyze_market(
        self,
        symbol: str,
        latest_price: float,
        indicators_summary: dict,
        recent_data_text: str = "",
        fundamentals_text: str = "",
    ) -> str:
        """调用大模型进行市场分析"""
        system_prompt = (
            "你是一位专业量化交易分析师。请用中文给出简洁、明确的技术分析，"
            "重点覆盖趋势、风险、估值参照、操作建议和最终信号。不要展开长篇解释。"
            "如果标的是场外基金（fund），不要基于成交量判断。"
        )

        user_prompt = f"标的: {symbol}\n最新价格: {latest_price}\n技术指标摘要:\n"
        for k, v in indicators_summary.items():
            user_prompt += f"  - {k}: {v}\n"

        if recent_data_text:
            user_prompt += f"\n近期数据:\n{recent_data_text}\n"

        if fundamentals_text:
            user_prompt += f"\n公司财务与营业模式摘要:\n{fundamentals_text}\n"

        user_prompt += (
            "\n请用不超过 420 字输出，格式如下:\n"
            "趋势: ...\n"
            "风险: ...\n"
            "财务: 若是股票，概括现金流、盈利能力和营业模式；非股票则写不适用...\n"
            "估值: 用股票收益率E/P、债券收益率YTM、房地产Cap Rate、收购EV/FCF作相对参照...\n"
            "建议: ...\n"
            "关注: ...\n"
            "\n【非常重要】请在报告最后单独输出一行:\n"
            "信号: 买入 / 卖出 / 观望 （三选一，必须明确）\n"
        )

        return self.chat(system_prompt, user_prompt)

    def interpret_user_request(self, user_input: str) -> dict:
        """把自然语言请求解析成结构化动作"""
        system_prompt = (
            "你是量化交易终端的指令解析器。"
            "请把用户的中文请求解析成 JSON，不要输出任何多余文字。"
            "可用 intent: analyze, holdings, portfolio, risk, report, sentiment, help, quit, unknown。"
            "字段包括: intent, symbol, market, period, use_ai, reply。"
            "market 只能是 a_stock / us_stock / crypto / fund 之一或空字符串。"
            "period 只能是 1mo / 3mo / 6mo / 1y / 2y / 5y 之一或空字符串。"
            "use_ai 是布尔值。"
            "如果用户表达退出，intent=quit。"
            "如果用户要分析某个标的，intent=analyze，并尽量提取 symbol、market、period。"
            "如果无法确定，intent=unknown，并在 reply 里给一句简短提示。"
        )
        user_prompt = (
            "把下面请求解析成 JSON 对象:\n"
            f"{user_input}\n"
            '示例: {"intent":"analyze","symbol":"002982","market":"fund","period":"1y","use_ai":true,"reply":""}'
        )
        raw = self.chat(system_prompt, user_prompt).strip()

        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.replace("json", "", 1).strip()

        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        return {
            "intent": "unknown",
            "symbol": "",
            "market": "",
            "period": "",
            "use_ai": True,
            "reply": "我没能稳定解析这句话，请换一种更直接的说法。",
        }

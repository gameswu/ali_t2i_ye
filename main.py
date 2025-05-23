from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp
from astrbot.core.message.message_event_result import MessageChain

from dashscope import ImageSynthesis
import asyncio

@register("ali_t2i_ye", "gameswu", "利用阿里文生图ai绘画的插件", "0.1.0", "https://github.com/gameswu/ali_t2i_ye")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.api_key = config.get("api_key", "")
        self.model_name = config.get("model_name", "wanx2.1-t2i-turbo")

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
    
    async def generate_image(self, prompt, negative_prompt, size):
        """使用阿里云通义万相生成图像"""
        try:
            print(f"阿里云请求参数: model={self.model_name}, prompt={prompt}, negative_prompt={negative_prompt}, size={size}")

            # 创建异步任务
            task_rsp = ImageSynthesis.async_call(
                api_key=self.api_key,
                model=self.model_name,
                prompt=prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                n=1,
                size=size
            )
            
            print(f"阿里云提交响应状态码: {task_rsp.status_code}")
            
            if task_rsp.status_code != 200:
                raise Exception(f"任务提交失败: {task_rsp.message}")
            
            # 等待任务完成
            result_rsp = await asyncio.to_thread(ImageSynthesis.wait, task_rsp, api_key=self.api_key)
            
            print(f"阿里云结果响应状态码: {result_rsp.status_code}")
            
            if result_rsp.status_code == 200:
                results = result_rsp.output.results
                if results:
                    image_url = results[0].url
                    print(f"阿里云生成图片成功，URL: {image_url}")
                    return image_url
                else:
                    raise Exception("任务成功，但没有返回图像结果")
            else:
                raise Exception(f"任务失败: {result_rsp.message}")
        
        except Exception as e:
            # 详细打印完整错误信息
            import traceback
            error_message = f"阿里云通义万相生成图片失败: {str(e)}\n{traceback.format_exc()}"
            print(error_message)
            return None
        
    @filter.llm_tool("text2image")
    async def text2image(self, event: AstrMessageEvent, prompt: str, negative_prompt: str = ""):
        """根据文字绘图的工具

        Args:
            prompt(string): 生成图片的提示词
            negative_prompt(string): 生成图片的反向提示词，指导模型不生成什么内容
        """
        try:
            # 生成图片
            image_url = await self.generate_image(prompt, negative_prompt, "1024*1024")
            if image_url:
                # 发送生成的图片
                message = MessageChain([Comp.Image.fromURL(image_url)])
                await event.send(message)
                return f"生成图片成功，提示词: {prompt}，反向提示词: {negative_prompt}"
            else:
                return "生成图片失败"
        except Exception as e:
            logger.error(f"处理消息时发生错误: {str(e)}")
            return "处理消息时发生错误"

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

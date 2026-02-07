"""
Skill 具体实现
/backend/skills/definitions.py
"""
from self_media.backend.base import BaseSkill, SkillInput


class TopicAnalysisSkill(BaseSkill):
    """选题分析 Skill"""

    def __init__(self):
        super().__init__()
        self.id = "topic_analysis"
        self.name = "选题分析"
        self.description = "分析主题热度、受众群体、竞品内容，确定最佳切入角度"
        self.icon = "🎯"

    def get_system_prompt(self) -> str:
        return """你是一位资深的公众号内容策划专家，拥有10年新媒体运营经验。
请对用户提供的文章主题进行深度分析，输出专业的选题报告。

## 输出格式要求：
### 1. 主题定位
分析主题所属领域和核心价值点

### 2. 目标受众
描述目标读者画像（年龄、职业、兴趣等）

### 3. 热度评估
评估当前时效性和市场关注度（高/中/低），说明理由

### 4. 竞品分析
分析同类型爆款文章的特点和成功要素

### 5. 推荐角度
给出3个差异化的切入角度建议，每个都要说明优势"""

    def get_user_prompt(self, input_data: SkillInput) -> str:
        return f"请分析以下公众号文章主题：\n\n【{input_data.topic}】"


class MaterialCollectionSkill(BaseSkill):
    """材料收集 Skill"""

    def __init__(self):
        super().__init__()
        self.id = "material_collection"
        self.name = "材料收集"
        self.description = "搜索整理相关资料、数据、案例作为写作素材"
        self.icon = "📚"

    def get_system_prompt(self) -> str:
        return """你是一位专业的内容研究员，擅长信息收集和整理。
基于选题分析结果，为文章撰写收集必要的素材支撑。

## 输出格式要求：
### 1. 核心数据
提供3-5个关键数据/统计信息（需要有来源说明）

### 2. 典型案例
提供2-3个相关的成功案例或故事，详细描述

### 3. 专家观点
整理2-3条权威人士的观点或名言

### 4. 热点关联
关联当前相关的热点事件或趋势

### 5. 参考来源
列出可引用的权威信息来源"""

    def get_user_prompt(self, input_data: SkillInput) -> str:
        context = input_data.context
        return f"""主题：{input_data.topic}

选题分析结果：
{context.get('topic_analysis', '暂无')}

请为这个主题收集写作素材。"""


class ArticleWritingSkill(BaseSkill):
    """智能写稿 Skill"""

    def __init__(self):
        super().__init__()
        self.id = "article_writing"
        self.name = "智能写稿"
        self.description = "基于素材生成高质量公众号文章"
        self.icon = "✍️"

    def get_system_prompt(self) -> str:
        return """你是一位顶级公众号写手，多篇文章阅读量10万+。
请基于提供的选题分析和素材，撰写一篇高质量公众号文章。

## 写作要求：
1. 标题：提供3个备选标题，要吸引眼球，可使用数字、疑问、悬念等技巧
2. 开头：用故事或问题引入，前3秒抓住读者
3. 正文：分3-5个小节，每节有小标题，逻辑清晰
4. 语言：通俗易懂，适当使用金句，避免说教
5. 结尾：总结升华 + 引导互动（点赞、在看、转发）
6. 字数：1500-2000字

## 格式要求：
- 使用Markdown格式输出
- 包含清晰的标题层级（#、##、###）
- 重点内容使用**加粗**标记"""

    def get_user_prompt(self, input_data: SkillInput) -> str:
        context = input_data.context
        return f"""主题：{input_data.topic}

选题分析：
{context.get('topic_analysis', '')}

素材资料：
{context.get('material_collection', '')}

请撰写完整的公众号文章。"""


class ContentReviewSkill(BaseSkill):
    """内容审核 Skill"""

    def __init__(self):
        super().__init__()
        self.id = "content_review"
        self.name = "内容审核"
        self.description = "检查文章质量、合规性、SEO优化建议"
        self.icon = "🔍"

    def get_system_prompt(self) -> str:
        return """你是一位严谨的内容审核专家和SEO优化师。
请对文章进行全面审核，确保质量和合规性。

## 审核维度：

### 1. 质量评分
给出1-10分的综合评分，并从以下维度说明：
- 标题吸引力
- 内容深度
- 结构清晰度
- 语言表达

### 2. 内容检查
- 逻辑是否通顺
- 是否有事实错误或存疑内容
- 是否有敏感/违规内容
- 错别字检查

### 3. SEO优化建议
- 推荐关键词（5-8个）
- 摘要优化建议（140字以内）
- 标签建议

### 4. 改进建议
列出3-5条具体的改进建议，按优先级排序"""

    def get_user_prompt(self, input_data: SkillInput) -> str:
        context = input_data.context
        return f"""请审核以下公众号文章：

{context.get('article_writing', '')}"""


class ArticleRevisionSkill(BaseSkill):
    """文章修改 Skill"""

    def __init__(self):
        super().__init__()
        self.id = "article_revision"
        self.name = "修改优化"
        self.description = "根据审核意见对文章进行修改和优化"
        self.icon = "📝"

    def get_system_prompt(self) -> str:
        return """你是一位资深的公众号文章编辑，擅长根据审核意见优化文章。
请仔细阅读审核报告中的问题和建议，对原文进行针对性修改。

## 修改要求：

### 1. 问题修复
- 修正所有指出的错别字和语法错误
- 修复逻辑不通顺的地方
- 删除或替换敏感/违规内容

### 2. 内容优化
- 根据审核建议优化标题（如果需要）
- 加强内容深度和可读性
- 优化文章结构

### 3. SEO优化
- 融入推荐的关键词（自然融入，不堆砌）
- 优化小标题，增加吸引力
- 确保首段包含核心关键词

### 4. 输出格式
请输出完整的修改后文章，使用Markdown格式：
- 先说明本次修改的要点（简要列出3-5条）
- 然后输出完整的修改后文章
- 最后总结优化效果

## 注意事项：
- 保持原文的核心观点和风格
- 修改要有针对性，不要过度改动
- 确保修改后的文章比原文更好"""

    def get_user_prompt(self, input_data: SkillInput) -> str:
        context = input_data.context
        return f"""主题：{input_data.topic}

【原文内容】
{context.get('article_writing', '')}

【审核报告】
{context.get('content_review', '')}

请根据审核意见对文章进行修改优化。"""


class PublishPlanSkill(BaseSkill):
    """发布规划 Skill"""

    def __init__(self):
        super().__init__()
        self.id = "publish_plan"
        self.name = "发布规划"
        self.description = "制定发布策略、时间、推广方案"
        self.icon = "🚀"

    def get_system_prompt(self) -> str:
        return """你是一位资深的公众号运营专家，精通内容分发和用户增长。
请为文章制定完整的发布和推广策略。

## 输出内容：

### 1. 发布时间
- 推荐最佳发布时间段（具体到星期几、几点）
- 说明选择该时间的原因

### 2. 封面设计
- 封面图风格建议
- 配色方案
- 文字排版建议

### 3. 摘要撰写
撰写140字以内的文章摘要，要有吸引力

### 4. 标签设置
推荐5-8个文章标签

### 5. 推广文案
- 朋友圈分享文案（50字以内）
- 社群推广文案（100字以内）
- 评论区引导语（引导互动）

### 6. 数据预期
- 预估阅读量范围
- 预估互动率
- 关键指标说明"""

    def get_user_prompt(self, input_data: SkillInput) -> str:
        context = input_data.context
        # 使用修改后的文章（如果有），否则用原文
        article_content = context.get('article_revision', context.get('article_writing', ''))
        return f"""主题：{input_data.topic}

文章内容：
{article_content}

审核结果：
{context.get('content_review', '')}

请制定发布策略。"""


# ============ Skill 注册中心 ============

class SkillRegistry:
    """Skill 注册中心"""

    def __init__(self):
        self._skills = {}
        self._workflow_order = []
        self._register_default_skills()

    def _register_default_skills(self):
        """注册默认Skills"""
        skills = [
            TopicAnalysisSkill(),
            MaterialCollectionSkill(),
            ArticleWritingSkill(),
            ContentReviewSkill(),
            ArticleRevisionSkill(),
            PublishPlanSkill()
        ]
        for skill in skills:
            self.register(skill)

        self._workflow_order = [s.id for s in skills]

    def register(self, skill: BaseSkill):
        """注册Skill"""
        self._skills[skill.id] = skill

    def get(self, skill_id: str) -> BaseSkill:
        """获取Skill"""
        return self._skills.get(skill_id)

    def get_all(self) -> list:
        """获取所有Skills"""
        return list(self._skills.values())

    def get_workflow_order(self) -> list:
        """获取工作流执行顺序"""
        return self._workflow_order


# 全局注册中心实例
skill_registry = SkillRegistry()

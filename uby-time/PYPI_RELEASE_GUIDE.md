# UBY-Time PyPI 发布指南

## 前提条件

您的包已经成功构建并验证：
- ✅ `uby_time-0.1.0-py3-none-any.whl`
- ✅ `uby_time-0.1.0.tar.gz`
- ✅ 通过 `twine check` 验证

## 步骤1：注册账号

### 1.1 注册TestPyPI账号（推荐先测试）
1. 访问：https://test.pypi.org/account/register/
2. 填写用户名、邮箱、密码
3. 验证邮箱

### 1.2 注册PyPI账号（正式发布）
1. 访问：https://pypi.org/account/register/
2. 填写用户名、邮箱、密码
3. 验证邮箱

## 步骤2：生成API Token

### 2.1 TestPyPI API Token
1. 登录 https://test.pypi.org/
2. 点击右上角用户名 → "Account settings"
3. 滚动到 "API tokens" 部分
4. 点击 "Add API token"
5. Token name: `uby-time-testpypi`
6. Scope: "Entire account" 或选择特定项目
7. 点击 "Add token"
8. **重要**：复制生成的token（以 `pypi-` 开头），保存好，只显示一次！

### 2.2 PyPI API Token
1. 登录 https://pypi.org/
2. 重复上述步骤
3. Token name: `uby-time-pypi`
4. 保存token

## 步骤3：配置Twine（可选）

创建 `~/.pypirc` 文件来保存配置：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = <your-pypi-token>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = <your-testpypi-token>
```

**注意**：将 `<your-pypi-token>` 和 `<your-testpypi-token>` 替换为实际的token。

## 步骤4：上传到TestPyPI（测试）

```bash
cd uby-time
python -m twine upload --repository testpypi dist/*
```

当提示输入API token时，输入您的TestPyPI token。

### 验证TestPyPI上传
1. 访问：https://test.pypi.org/project/uby-time/
2. 检查包信息是否正确

### 测试安装
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ uby-time
```

## 步骤5：上传到PyPI（正式发布）

确认TestPyPI测试无误后：

```bash
python -m twine upload dist/*
```

当提示输入API token时，输入您的PyPI token。

### 验证PyPI上传
1. 访问：https://pypi.org/project/uby-time/
2. 检查包信息

### 测试正式安装
```bash
pip install uby-time
```

## 步骤6：验证发布

```python
# 测试基本功能
from uby_time import iso_to_uby, format_full
uby = iso_to_uby("2026-01-01T00:00:00Z")
print(format_full(uby))
```

## 常见问题

### Q1: 包名已存在
如果包名 `uby-time` 已被占用，您需要：
1. 选择新的包名（如 `uby-time-spec`）
2. 修改 `pyproject.toml` 中的 `name` 字段
3. 重新构建包

### Q2: 权限错误
确保：
- API token正确
- Token有足够权限
- 包名没有冲突

### Q3: 版本冲突
如果版本 `0.1.0` 已存在：
1. 修改 `pyproject.toml` 中的版本号
2. 重新构建包

## 安全建议

1. **不要在代码中硬编码API token**
2. **使用环境变量或配置文件**
3. **定期轮换API token**
4. **限制token权限范围**

## 发布后的维护

### 更新版本
1. 修改 `pyproject.toml` 中的版本号
2. 更新 `CHANGELOG.md`
3. 重新构建和上传

### 撤回版本（谨慎使用）
```bash
# 只能撤回72小时内的版本
python -m twine upload --repository pypi --skip-existing dist/*
```

## 当前状态

- ✅ 包已构建完成
- ✅ 包已通过验证
- ⏳ 等待注册PyPI账号
- ⏳ 等待生成API token
- ⏳ 等待上传

## 下一步

1. 注册TestPyPI和PyPI账号
2. 生成API token
3. 先上传到TestPyPI测试
4. 确认无误后上传到PyPI

祝您发布顺利！🚀

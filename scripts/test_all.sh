#!/bin/bash
# ChatAgentCore 自动化测试脚本
# 按顺序执行各平台测试工具，输出测试报告

set -e  # 遇到错误立即退出

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TEST_RESULTS=()
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 打印带颜色的消息
print_header() {
    echo -e "${GREEN}*** $1 ***${NC}"
}

print_success() {
    echo -e "${GREEN}[OK] $1${NC}"
}

print_error() {
    echo -e "${RED}[X] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

print_section() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
}

# 测试函数
test_verify_setup() {
    local name="环境验证"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    print_section "1. 环境验证"
    if python3 scripts/verify_setup.py; then
        print_success "$name"
        TEST_RESULTS+=("$name: 通过")
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_error "$name"
        TEST_RESULTS+=("$name: 失败")
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

test_feishu() {
    local name="飞书适配器测试"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    print_section "2. 飞书适配器测试"

    # 检查是否启用
    if python3 -c "import yaml; config = yaml.safe_load(open('config/config.yaml')); print(config['platforms']['feishu']['enabled'])" 2>/dev/null | grep -q "True"; then
        print_warning "飞书测试需要人工交互，跳过自动测试"
        print_warning "手动测试: python3 cli/test_feishu_ws.py"
        TEST_RESULTS+=("$name: 跳过 (需要人工交互)")
        return 0
    else
        print_warning "飞书平台未启用，跳过测试"
        TEST_RESULTS+=("$name: 跳过 (未启用)")
        return 0
    fi
}

test_weixin_login() {
    local name="微信适配器测试"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    print_section "3. 微信适配器测试"

    # 检查是否启用
    if ! python3 -c "import yaml; config = yaml.safe_load(open('config/config.yaml')); print(config['platforms'].get('weixin', {}).get('enabled', False))" 2>/dev/null | grep -q "True"; then
        print_warning "微信平台未启用，跳过测试"
        TEST_RESULTS+=("$name: 跳过 (未启用)")
        return 0
    fi

    print_warning "微信测试需要人工交互，跳过自动测试"
    print_warning "手动测试: python3 cli/test_weixin.py login"
    print_warning "手动测试: python3 cli/test_weixin.py receive --duration 60"
    TEST_RESULTS+=("$name: 跳过 (需要人工交互)")
    return 0
}

test_health_check() {
    local name="健康检查"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    print_section "4. 健康检查"

    # 检查服务是否运行
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "$name"
        TEST_RESULTS+=("$name: 通过")
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_warning "服务未运行，无法进行健康检查"
        print_warning "启动服务: python3 main.py"
        TEST_RESULTS+=("$name: 跳过 (服务未运行)")
        return 0
    fi
}

print_report() {
    print_section "测试报告"

    for result in "${TEST_RESULTS[@]}"; do
        echo "  - $result"
    done

    echo ""
    echo "总计: $TOTAL_TESTS | 通过: $PASSED_TESTS | 失败: $FAILED_TESTS | 跳过: $((TOTAL_TESTS - PASSED_TESTS - FAILED_TESTS))"

    if [ $FAILED_TESTS -eq 0 ]; then
        print_success "所有测试完成！"
        return 0
    else
        print_error "有 $FAILED_TESTS 个测试失败"
        return 1
    fi
}

# 主函数
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║        ChatAgentCore 自动化测试                      ║"
    echo "╚═══════════════════════════════════════════════════════╝"

    # 执行测试
    test_verify_setup
    test_feishu
    test_weixin_login
    test_health_check

    # 打印报告
    print_report

    return $?
}

# 运行主函数
main
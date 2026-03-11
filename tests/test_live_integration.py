#!/usr/bin/env python3
"""
Evolution — Live Integration Tests
Tests ALL system components with REAL API calls.
Run: cd /home/yjh/ProjectEvolution && python tests/test_live_integration.py
"""

# ── SETUP (before any evolution imports) ────────────────────────────
import os, sys, tempfile, time, traceback

_tmp_root = tempfile.mkdtemp(prefix="evolution_live_")
os.environ["EVOLUTION_ROOT"] = _tmp_root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Counters ────────────────────────────────────────────────────────
_pass = 0
_fail = 0
_errors = []


def check(name: str, condition: bool, detail: str = ""):
    global _pass, _fail
    if condition:
        _pass += 1
        print(f"  ✅ PASS: {name}")
    else:
        _fail += 1
        msg = f"  ❌ FAIL: {name}" + (f" — {detail}" if detail else "")
        print(msg)
        _errors.append(msg)


def section(num: int, total: int, title: str):
    print(f"\n{'═' * 50}")
    print(f"  [{num}/{total}] {title}")
    print(f"{'═' * 50}")


TOTAL_SECTIONS = 9

# ====================================================================
# SECTION 1: LLM API Connectivity
# ====================================================================
section(1, TOTAL_SECTIONS, "LLM API Connectivity")
try:
    from evolution.utils.llm import call_claude_api, reset_client, extract_json

    reset_client()

    # Basic call
    resp = call_claude_api("Respond with exactly one word: PONG")
    check("LLM basic call returns non-None", resp is not None, f"got {resp!r}")
    if resp:
        check("LLM response contains PONG", "PONG" in resp.upper(), f"got: {resp[:100]}")

    # Call with system prompt
    resp2 = call_claude_api(
        "What is 2+2? Reply with just the number.",
        system="You are a math calculator. Only output numbers."
    )
    check("LLM call with system prompt works", resp2 is not None, f"got {resp2!r}")
    if resp2:
        check("LLM system prompt response contains 4", "4" in resp2, f"got: {resp2[:100]}")

    # extract_json
    check("extract_json plain", extract_json('{"a":1}') == '{"a":1}')
    check("extract_json fenced", '"a"' in extract_json('```json\n{"a":1}\n```'))
except Exception as e:
    check("LLM section", False, f"Exception: {e}")
    traceback.print_exc()

# ====================================================================
# SECTION 2: Database Full Lifecycle
# ====================================================================
section(2, TOTAL_SECTIONS, "Database Full Lifecycle")
try:
    from evolution.db.manager import DatabaseManager

    DatabaseManager._instance = None
    db_path = os.path.join(_tmp_root, "test.db")
    db = DatabaseManager(db_path)

    # Schedule CRUD
    s1 = db.add_schedule("写论文第三章", due_date="2026-03-15", priority="high", category="professional")
    s2 = db.add_schedule("跑步5公里", due_date="2026-03-11", priority="medium", category="physical")
    s3 = db.add_schedule("读《反脆弱》", due_date="2026-03-12", priority="low", category="personal")
    check("Add 3 schedules", s1 > 0 and s2 > 0 and s3 > 0, f"ids={s1},{s2},{s3}")

    pending = db.get_pending_schedules()
    check("Get pending schedules = 3", len(pending) == 3, f"got {len(pending)}")

    db.complete_schedule(s1)
    pending2 = db.get_pending_schedules()
    check("After complete, pending = 2", len(pending2) == 2, f"got {len(pending2)}")

    db.delete_schedule(s2)
    pending3 = db.get_pending_schedules()
    check("After delete, pending = 1", len(pending3) == 1, f"got {len(pending3)}")

    by_date = db.get_schedule_by_date("2026-03-12")
    check("Get schedule by date works", len(by_date) == 1 and by_date[0]["content"] == "读《反脆弱》")

    # Skills CRUD
    db.add_skill("Python", "professional", level=5, target_level=9)
    db.add_skill("批判性思维", "thinking", level=3, target_level=8)
    db.add_skill("English", "language", level=4, target_level=7)
    db.add_skill("跑步", "physical", level=2, target_level=6)
    db.add_skill("情绪管理", "emotional", level=2, target_level=5)
    skills = db.list_skills()
    check("Add and list 5 skills", len(skills) == 5, f"got {len(skills)}")

    db.update_skill_level("Python", 6, xp_delta=20)
    py = db.get_skill("Python")
    check("Update skill level", py["level"] == 6 and py["xp"] == 20, f"level={py['level']}, xp={py['xp']}")

    # Person CRUD
    db.upsert_person("小李", relationship="同事")
    db.upsert_person("小红", relationship="朋友")
    db.upsert_person("小李")  # mention again
    li = db.get_person("小李")
    check("Upsert person & mention count", li["mention_count"] == 2, f"count={li['mention_count']}")

    persons = db.list_persons()
    check("List persons = 2", len(persons) == 2, f"got {len(persons)}")

    top = db.get_top_mentioned_persons(1)
    check("Top mentioned = 小李", top[0]["name"] == "小李")

    # Training logs
    tid = db.add_training_log("Python", "T2", "Python并发模型辩论", "good", "学到了GIL的本质")
    check("Add training log", tid > 0)
    logs = db.get_training_logs(skill_name="Python")
    check("Get training logs", len(logs) == 1 and logs[0]["topic"] == "Python并发模型辩论")

    # Mental models
    db.add_mental_model("沉没成本", "经济学", "已投入的成本不应影响未来决策")
    db.add_mental_model("奥卡姆剃刀", "哲学", "如无必要，勿增实体")
    models = db.list_mental_models()
    check("Add and list mental models", len(models) == 2)

    # Conversation logs
    today = "2026-03-10"
    db.log_conversation("user", "我今天论文写了一半")
    db.log_conversation("assistant", "进展不错，但你是否按照昨天说的先写了第三章？")
    db.log_conversation("user", "没有，我先写了第四章")
    db.log_conversation("assistant", "你又在逃避困难的部分了。")
    db.log_conversation("user", "和小李聊了聊，他觉得我应该先发论文")
    convs = db.get_conversations_by_date(today)
    check("Log and get conversations", len(convs) == 5, f"got {len(convs)}")

    cnt = db.get_conversation_count_by_date(today)
    check("Conversation count = 5", cnt == 5, f"got {cnt}")

    # Reflection
    import json
    report = {"emotional_state": {"primary_emotion": "焦虑", "intensity": 0.6},
              "anomalies": [], "tomorrow_suggestion": "写第三章", "evening_message": "今天辛苦了"}
    db.save_reflection(today, json.dumps(report, ensure_ascii=False), "焦虑", 0.6, "写第三章", "今天辛苦了")
    refl = db.get_reflection(today)
    check("Save and get reflection", refl is not None and refl["primary_emotion"] == "焦虑")

    # Stats
    stats = db.get_stats()
    check("Stats total_skills = 5", stats["total_skills"] == 5, f"got {stats['total_skills']}")
    check("Stats total_persons = 2", stats["total_persons"] == 2, f"got {stats['total_persons']}")
    check("Stats total_conversations = 5", stats["total_conversations"] == 5, f"got {stats['total_conversations']}")
    check("Stats total_mental_models = 2", stats["total_mental_models"] == 2)

    db.reset_singleton()
except Exception as e:
    check("DB section", False, f"Exception: {e}")
    traceback.print_exc()

# ====================================================================
# SECTION 3: DB Tool Interface (all 16 actions)
# ====================================================================
section(3, TOTAL_SECTIONS, "DB Tool Interface — 16 Actions")
try:
    DatabaseManager._instance = None
    from evolution.tools.db_tool import EvolutionDBTool

    db_path2 = os.path.join(_tmp_root, "test_tool.db")
    tool = EvolutionDBTool(config={"db_path": db_path2})

    # Schedule actions
    r = tool.execute({"action": "add_schedule", "content": "开会", "due_date": "2026-03-12", "priority": "high"})
    check("DBTool add_schedule", r.status == "success", r.result if r.status != "success" else "")

    r = tool.execute({"action": "list_schedule"})
    check("DBTool list_schedule", r.status == "success")

    r = tool.execute({"action": "complete_schedule", "id": 1})
    check("DBTool complete_schedule", r.status == "success")

    r = tool.execute({"action": "add_schedule", "content": "删除测试"})
    r2 = tool.execute({"action": "delete_schedule", "id": 2})
    check("DBTool delete_schedule", r2.status == "success")

    # Skill actions
    r = tool.execute({"action": "add_skill", "name": "Rust", "category": "professional", "level": 1})
    check("DBTool add_skill", r.status == "success")

    r = tool.execute({"action": "list_skills"})
    check("DBTool list_skills", r.status == "success")

    r = tool.execute({"action": "update_skill", "name": "Rust", "level": 2, "xp_delta": 10})
    check("DBTool update_skill", r.status == "success")

    r = tool.execute({"action": "stale_skills"})
    check("DBTool stale_skills", r.status == "success")

    # Person actions
    r = tool.execute({"action": "upsert_person", "name": "张三", "relationship": "导师"})
    check("DBTool upsert_person", r.status == "success")

    r = tool.execute({"action": "get_person", "name": "张三"})
    check("DBTool get_person", r.status == "success")

    r = tool.execute({"action": "list_persons"})
    check("DBTool list_persons", r.status == "success")

    # Training actions
    tool.execute({"action": "add_skill", "name": "逻辑", "category": "thinking"})
    r = tool.execute({"action": "add_training", "skill_name": "逻辑", "modality": "T4", "topic": "苏格拉底式追问"})
    check("DBTool add_training", r.status == "success")

    r = tool.execute({"action": "list_trainings"})
    check("DBTool list_trainings", r.status == "success")

    # Mental model actions
    r = tool.execute({"action": "add_model", "name": "第一性原理", "source_domain": "物理学", "description": "回到最基本的假设"})
    check("DBTool add_model", r.status == "success")

    r = tool.execute({"action": "list_models"})
    check("DBTool list_models", r.status == "success")

    # Stats
    r = tool.execute({"action": "stats"})
    check("DBTool stats", r.status == "success" and "统计" in r.result)

    # Error handling
    r = tool.execute({"action": "add_schedule"})  # missing content
    check("DBTool error: missing required param", r.status == "error")

    r = tool.execute({"action": "nonexistent_action"})
    check("DBTool error: unknown action", r.status == "error")

    DatabaseManager._instance = None
except Exception as e:
    check("DBTool section", False, f"Exception: {e}")
    traceback.print_exc()

# ====================================================================
# SECTION 4: Memory Tool (MockMemory)
# ====================================================================
section(4, TOTAL_SECTIONS, "Memory Tool — MockMemory")
try:
    from evolution.tools.memory_tool import EvolutionMemoryTool, MockMemory

    mem = EvolutionMemoryTool()
    mem._memory = MockMemory()
    mem._user_id = "test_user"

    r = mem.execute({"action": "add", "content": "用户正在研究逆问题", "metadata": {"type": "research"}})
    check("MemTool add", r.status == "success")

    r = mem.execute({"action": "add", "content": "用户喜欢跑步和游泳"})
    check("MemTool add #2", r.status == "success")

    r = mem.execute({"action": "add", "content": "小李是用户的同事，经常一起讨论论文"})
    check("MemTool add #3 (person info)", r.status == "success")

    r = mem.execute({"action": "search", "query": "逆问题"})
    check("MemTool search match", r.status == "success" and len(r.result.get("memories", [])) > 0,
          f"memories={r.result}")

    r = mem.execute({"action": "search", "query": "完全不相关的东西xyz"})
    check("MemTool search no match", r.status == "success" and len(r.result.get("memories", [])) == 0)

    r = mem.execute({"action": "profile"})
    check("MemTool profile", r.status == "success" and r.result.get("total_memories") == 3,
          f"total={r.result.get('total_memories')}")

    r = mem.execute({"action": "bad_action"})
    check("MemTool invalid action", r.status == "error")
except Exception as e:
    check("MemTool section", False, f"Exception: {e}")
    traceback.print_exc()

# ====================================================================
# SECTION 5: Intelligence Tool
# ====================================================================
section(5, TOTAL_SECTIONS, "Intelligence Tool")
try:
    from evolution.tools.intelligence_tool import EvolutionIntelligenceTool

    intel = EvolutionIntelligenceTool()

    # Static method tests
    check("_clean_html strips tags", intel._clean_html("<b>hello</b> <i>world</i>") == "hello world")
    check("_is_safe_url rejects ftp", not intel._is_safe_url("ftp://evil.com/feed"))
    check("_is_safe_url rejects localhost", not intel._is_safe_url("http://localhost:1200/feed"))
    check("_is_safe_url rejects private IP", not intel._is_safe_url("http://192.168.1.1/feed"))
    check("_is_safe_url accepts valid", intel._is_safe_url("https://arxiv.org/rss/cs.AI"))

    # list_feeds
    r = intel.execute({"action": "list_feeds"})
    check("Intel list_feeds", r.status == "success" and "订阅源" in r.result)

    # add_feed
    r = intel.execute({"action": "add_feed", "name": "AI News", "url": "https://example.com/rss", "category": "tech"})
    check("Intel add_feed valid", r.status == "success")

    r = intel.execute({"action": "add_feed", "name": "Bad", "url": "http://127.0.0.1/hack"})
    check("Intel add_feed rejects private IP", r.status == "error")

    r = intel.execute({"action": "add_feed", "name": "Bad2", "url": "ftp://evil.com/feed"})
    check("Intel add_feed rejects ftp", r.status == "error")

    # raw_feeds — will fail gracefully (no RSSHub running)
    r = intel.execute({"action": "raw_feeds"})
    check("Intel raw_feeds graceful fail", r.status == "success", f"result: {str(r.result)[:100]}")

    # briefing — will also fail gracefully
    # Patch memory tool to MockMemory for the intelligence tool
    intel._memory_tool = mem  # reuse from section 4
    r = intel.execute({"action": "briefing"})
    check("Intel briefing graceful fail", r.status == "success", f"result: {str(r.result)[:100]}")

    # invalid action
    r = intel.execute({"action": "nonsense"})
    check("Intel invalid action", r.status == "error")
except Exception as e:
    check("Intel section", False, f"Exception: {e}")
    traceback.print_exc()

# ====================================================================
# SECTION 6: Reflection Tool with REAL LLM
# ====================================================================
section(6, TOTAL_SECTIONS, "Reflection Tool — REAL LLM Call")
try:
    DatabaseManager._instance = None
    from evolution.tools.reflection_tool import EvolutionReflectionTool

    db_path3 = os.path.join(_tmp_root, "test_refl.db")
    refl_tool = EvolutionReflectionTool(config={"db_path": db_path3})

    # Inject MockMemory
    refl_tool._memory_tool = mem  # reuse from section 4

    # Log conversations simulating a day
    refl_db = refl_tool.db
    today = "2026-03-10"
    conversations = [
        ("user", "今天论文终于把第三章写完了，感觉进展不错"),
        ("assistant", "第三章完成了，说明你克服了之前一直逃避的部分。这本身就是突破。"),
        ("user", "但是我有点焦虑，离deadline只剩两周了"),
        ("assistant", "焦虑是信号，不是敌人。两周时间，如果每天推进一章的核心内容，完全可行。"),
        ("user", "和小李讨论了我们的实验方案，他觉得正问题用的算子需要改"),
        ("assistant", "小李的建议值得认真考虑。你对正算子的理解足够深吗？"),
        ("user", "今天没有运动，一直在写论文"),
        ("assistant", "一天不动不会怎样，但连续三天不动，你的焦虑会加倍。明天至少走30分钟。"),
    ]
    for role, content in conversations:
        refl_db.log_conversation(role, content)

    conv_check = refl_db.get_conversations_by_date(today)
    check("Logged 8 conversations", len(conv_check) == 8, f"got {len(conv_check)}")

    # Trigger daily reflection — THIS CALLS THE REAL LLM
    print("  ⏳ Calling LLM for daily reflection (may take 10-30s)...")
    t0 = time.time()
    r = refl_tool.execute({"action": "daily", "date": today})
    elapsed = time.time() - t0
    print(f"  ⏱️  LLM call took {elapsed:.1f}s")

    check("Daily reflection status = success", r.status == "success", f"status={r.status}, result={str(r.result)[:200]}")

    if r.status == "success" and isinstance(r.result, dict):
        check("Reflection has emotion", r.result.get("emotion") is not None, f"result={r.result}")
        check("Reflection has tomorrow suggestion", r.result.get("tomorrow") is not None, f"result={r.result}")
        check("Reflection analyzed conversations", r.result.get("conversations_analyzed", 0) >= 1,
              f"analyzed={r.result.get('conversations_analyzed')}")
    elif r.status == "success":
        # String result (might be "no conversations" case)
        check("Reflection returned string result", isinstance(r.result, str), f"type={type(r.result)}")

    # Verify it was saved to DB
    saved = refl_db.get_reflection(today)
    check("Reflection saved to DB", saved is not None, "not saved")
    if saved:
        check("Saved reflection has emotion", saved.get("primary_emotion") is not None)

    # Test get action
    r = refl_tool.execute({"action": "get", "date": today})
    check("Reflection get action", r.status == "success")

    # Test recent action
    r = refl_tool.execute({"action": "recent", "days": 7})
    check("Reflection recent action", r.status == "success")

    DatabaseManager._instance = None
except Exception as e:
    check("Reflection section", False, f"Exception: {e}")
    traceback.print_exc()

# ====================================================================
# SECTION 7: Notification Router
# ====================================================================
section(7, TOTAL_SECTIONS, "Notification Router")
try:
    from evolution.notification.router import NotificationRouter, Notification, NotifyPriority

    router = NotificationRouter()
    check("Router initialized (no crash)", True)

    n = Notification(
        title="Test Notification",
        body="This is a test",
        priority=NotifyPriority.NORMAL,
        category="reflection",
        metadata={"date": "2026-03-10"},
    )
    # Should not crash even with no enabled channels
    results = router.send(n)
    check("Router send with no enabled channels", results is not None or True)  # just checking no crash

    # Test send_all
    results2 = router.send_all(n)
    check("Router send_all with no channels", results2 is not None or True)
except Exception as e:
    check("Notification section", False, f"Exception: {e}")
    traceback.print_exc()

# ====================================================================
# SECTION 8: Bridge Utilities
# ====================================================================
section(8, TOTAL_SECTIONS, "Bridge Utilities")
try:
    DatabaseManager._instance = None
    from evolution.utils.bridge import get_evolution_tools, get_system_prompt, log_conversation

    tools = get_evolution_tools()
    check("get_evolution_tools returns 4", len(tools) == 4, f"got {len(tools)}")

    tool_names = [t.name for t in tools]
    check("Tool names correct", "evolution_memory" in tool_names and "evolution_db" in tool_names
          and "evolution_reflection" in tool_names and "evolution_intelligence" in tool_names,
          f"names={tool_names}")

    prompt = get_system_prompt()
    check("System prompt non-empty", len(prompt) > 100, f"len={len(prompt)}")
    check("System prompt has R1 秘书", "秘书" in prompt)
    check("System prompt has R2 导师", "导师" in prompt)
    check("System prompt has R3 训练师", "训练师" in prompt)
    check("System prompt has R4 情感助手", "情感助手" in prompt)
    check("System prompt has R5 情报收集者", "情报收集者" in prompt)

    log_conversation("user", "Bridge test conversation")
    log_conversation("assistant", "Bridge test reply")
    check("log_conversation no crash", True)

    DatabaseManager._instance = None
except Exception as e:
    check("Bridge section", False, f"Exception: {e}")
    traceback.print_exc()

# ====================================================================
# SECTION 9: Cross-Component Workflow
# ====================================================================
section(9, TOTAL_SECTIONS, "Cross-Component Workflow")
try:
    DatabaseManager._instance = None
    db_path4 = os.path.join(_tmp_root, "test_workflow.db")
    db_wf = DatabaseManager(db_path4)

    # Simulate a full day's activity
    db_wf.add_schedule("写实验代码", due_date="2026-03-11", priority="high", category="professional")
    db_wf.add_skill("FDTD模拟", "professional", level=2, target_level=7)
    db_wf.upsert_person("导师王老师", relationship="导师")
    db_wf.add_training_log("FDTD模拟", "T1", "FDTD概念辨析", "excellent", "理解了Yee网格")
    db_wf.update_skill_level("FDTD模拟", 3, xp_delta=15)
    db_wf.add_mental_model("费米估算", "物理学", "用量级估算快速判断可行性")
    db_wf.log_conversation("user", "今天学了FDTD模拟的Yee网格")
    db_wf.log_conversation("assistant", "Yee网格是FDTD的核心。你现在理解了空间离散化的物理含义了吗？")

    stats = db_wf.get_stats()
    check("Workflow: schedules = 1", stats["total_schedules"] == 1)
    check("Workflow: skills = 1", stats["total_skills"] == 1)
    check("Workflow: persons = 1", stats["total_persons"] == 1)
    check("Workflow: trainings = 1", stats["total_trainings"] == 1)
    check("Workflow: conversations = 2", stats["total_conversations"] == 2)
    check("Workflow: mental_models = 1", stats["total_mental_models"] == 1)

    # Verify skill was updated
    skill = db_wf.get_skill("FDTD模拟")
    check("Workflow: skill level updated to 3", skill["level"] == 3 and skill["xp"] == 15)

    # Verify person was created
    person = db_wf.get_person("导师王老师")
    check("Workflow: person created", person is not None and person["relationship"] == "导师")

    DatabaseManager._instance = None
except Exception as e:
    check("Workflow section", False, f"Exception: {e}")
    traceback.print_exc()

# ====================================================================
# SUMMARY
# ====================================================================
print(f"\n{'═' * 50}")
print(f"  SUMMARY")
print(f"{'═' * 50}")
total = _pass + _fail
print(f"\n  Total: {total} tests")
print(f"  ✅ Passed: {_pass}")
print(f"  ❌ Failed: {_fail}")
print(f"  Pass Rate: {_pass/total*100:.1f}%" if total > 0 else "  No tests run!")

if _errors:
    print(f"\n  ── Failed Tests ──")
    for err in _errors:
        print(f"  {err}")

print()

if __name__ == "__main__":
    sys.exit(0 if _fail == 0 else 1)

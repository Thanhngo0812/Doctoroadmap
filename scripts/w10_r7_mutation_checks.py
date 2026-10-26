"""Sequential W10 R7 mutations; run with no full gate or browser on this tree."""
from pathlib import Path
import w10_mutation_checks as checks
ROOT=Path(__file__).resolve().parents[1]
checks.OUT=ROOT/'report/w10-r7-evidence/mutations-existing'
checks.RUN='mutations-r7-existing'
assert checks.main()==0
checks.OUT=ROOT/'report/w10-r7-evidence/mutations-required'
checks.RUN='mutations-r7-required'
checks.TEST='src/web/backend/tests/test_content_admission_w10.py::'
B='src/web/backend/wayfinder/'
F='src/web/frontend/src/'
checks.cases=[
 ('assistant-admission',B+'infrastructure/learning_runtime.py','            self.document_requests.admit(owner)','            pass # mutation: bypass document admission', 'test_documents_per_hour_applies_across_button_and_assistant'),
 ('quota-lock',B+'infrastructure/document_requests.py',"SELECT pg_advisory_xact_lock(hashtextextended(:bucket,0))",'SELECT 1','test_admission_waits_for_the_other_postgres_runtime_before_rechecking_the_last_slot'),
 ('tool-error-code',B+'infrastructure/assistant_tools.py',"'code': error.code","'code': 'tool_error'",'test_hourly_document_limit_has_safe_tool_error_and_persistent_public_chat_notice'),
 ('tool-error-message',B+'infrastructure/assistant_tools.py',"'message': error.message","'message': 'Internal error'",'test_hourly_document_limit_has_safe_tool_error_and_persistent_public_chat_notice'),
 ('late-success',F+'ContentPages.tsx',"const grade = await submitQuiz(cid, quiz.attempt_id, answers);\n      if (submitting.current !== request) return;","const grade = await submitQuiz(cid, quiz.attempt_id, answers);",'react'),
 ('late-error',F+'ContentPages.tsx',"} catch (cause) {\n      if (submitting.current !== request) return;","} catch (cause) {",'react'),
 ('late-finally',F+'ContentPages.tsx','if (submitting.current === request) { submitting.current = null; setSending(false); }','{ submitting.current = null; setSending(false); }','react'),
]
assert checks.main()==0

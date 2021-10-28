import time

from builder.actions import update_code_statuses
from codelists.models import CodelistVersion


def run():
    code = "5505005"
    draft = CodelistVersion.objects.get_by_hash("6463fc2f")

    status = draft.code_objs.get(code=code).status
    new_status = {"+": "-", "-": "+"}[status]
    t0 = time.time()
    print(t0)
    # update_code_statuses(draft=draft, updates=[("", new_status)])
    print(len(draft.codes))
    print(time.time() - t0)

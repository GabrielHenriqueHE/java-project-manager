from manager.models import DirectoryRole

GROUP_ID = "org.codehaus.mojo"
ARTIFACT_ID = "build-helper-maven-plugin"
VERSION = "3.6.0"

ROLE_GOAL_PHASE: dict[DirectoryRole, tuple[str, str]] = {
    "source": ("add-source", "generate-sources"),
    "test-source": ("add-test-source", "generate-test-sources"),
    "resource": ("add-resource", "generate-resources"),
    "test-resource": ("add-test-resource", "generate-test-resources"),
}

GOAL_ROLE: dict[str, DirectoryRole] = {
    goal: role for role, (goal, _phase) in ROLE_GOAL_PHASE.items()
}

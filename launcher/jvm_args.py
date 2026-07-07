from typing import Iterable, List


def ram_jvm_args(ram_mb: int) -> List[str]:
    ram_mb = max(1024, int(ram_mb))
    return [f"-Xmx{ram_mb}M", f"-Xms{max(512, ram_mb // 2)}M"]


def merge_jvm_args(api_jvm: Iterable[str], ram_mb: int, extra: Iterable[str] = ()) -> List[str]:
    filtered = [
        a for a in api_jvm
        if not (isinstance(a, str) and (a.startswith("-Xmx") or a.startswith("-Xms")))
    ]
    merged = ram_jvm_args(ram_mb) + list(filtered)
    for arg in extra:
        if arg and arg not in merged:
            merged.append(arg)
    return merged

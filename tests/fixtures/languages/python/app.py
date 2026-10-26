"""供 Repoize 提取项目事实的最小可运行样例。"""


def greet(name: str = "world") -> str:
    return f"Hello, {name}!"


def main() -> None:
    print(greet())


if __name__ == "__main__":
    main()

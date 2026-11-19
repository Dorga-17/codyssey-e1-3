import json
import time
from pathlib import Path


def calculate_mac(pattern, filter_matrix):
    total = 0.0
    size = len(pattern)

    for row in range(size):
        for col in range(size):
            total += pattern[row][col] * filter_matrix[row][col]

    return total


def measure_mac_time(pattern, filter_matrix):
    start_time = time.perf_counter()

    score = calculate_mac(pattern, filter_matrix)

    end_time = time.perf_counter()

    elapsed_ms = (end_time - start_time) * 1000

    return score, elapsed_ms


def measure_mac_repeated(pattern, filter_matrix, repetitions=10):
    if (
        isinstance(repetitions, bool)
        or not isinstance(repetitions, int)
        or repetitions < 10
    ):
        raise ValueError("반복 횟수는 10 이상의 정수여야 합니다.")

    measured_times = []
    reference_score = None

    for _ in range(repetitions):
        score, elapsed_ms = measure_mac_time(
            pattern, filter_matrix
        )

        if reference_score is None:
            reference_score = score

        elif score != reference_score:
            raise ValueError(
                "반복 측정 중 MAC 점수가 달라졌습니다."
            )

        measured_times.append(elapsed_ms)

    average_ms = sum(measured_times) / repetitions

    return {
        "score": reference_score,
        "average_ms": average_ms,
        "repetitions": repetitions,
        "times_ms": measured_times,
    }


def collect_performance_results(repetitions=10):
    if (
        isinstance(repetitions, bool)
        or not isinstance(repetitions, int)
        or repetitions < 10
    ):
        raise ValueError("반복 횟수는 10 이상의 정수여야 합니다.")

    results = []

    for size in (3, 5, 13, 25):
        cross_filter = generate_pattern(size, "Cross")
        x_filter = generate_pattern(size, "X")

        for pattern_type in ("Cross", "X"):
            pattern = generate_pattern(size, pattern_type)

            cross_result = measure_mac_repeated(
                pattern, cross_filter, repetitions
            )

            x_result = measure_mac_repeated(
                pattern, x_filter, repetitions
            )

            prediction = classify_scores(
                cross_result["score"],
                x_result["score"],
                label_a="Cross",
                label_b="X",
            )

            results.append({
                "size": size,
                "mac_operations": size * size,
                "pattern_type": pattern_type,
                "cross_score": cross_result["score"],
                "x_score":x_result["score"],
                "cross_average_ms": cross_result["average_ms"],
                "x_average_ms": x_result["average_ms"],
                "prediction": prediction,
                "repetitions": repetitions,
            })

    return results


def read_matrix(label, size=3):
    print(f"\n{label} ({size}줄 입력, 공백 구분)")

    matrix = []

    for row_index in range(size):
        while True:
            user_input = input(f"{row_index + 1}행 : ")
            values = user_input.split()

            if len(values) != size:
                print(
                    f"입력 형식 오류 : 각 줄에 {size}개의 숫자를 "
                    "공백으로 구분해 입력하세요."
                )
                continue

            try:
                row = [float(value) for value in values]
            except ValueError:
                print("입력 형식 오류 : 숫자만 입력하세요.")
                continue

            matrix.append(row)
            break

    return matrix


def classify_scores(score_a, score_b, label_a="A", label_b="B", epsilon=1e-9):
    if abs(score_a - score_b) < epsilon:
        return "UNDECIDED"

    if score_a > score_b:
        return label_a

    return label_b


def load_json_data():
    data_path = Path(__file__).resolve().parent / "data.json"

    try:
        with data_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        print("파일 오류 : data.json을 찾을 수 없습니다.")

    except json.JSONDecodeError as error:
        print(f"JSON 문법 오류 : {error}")

    except OSError as error:
        print(f"파일 읽기 오류 : {error}")

    return None


def select_filters_for_pattern(data, pattern_key):
    parts = pattern_key.split("_")

    if (
        len(parts) != 3
        or parts[0] != "size"
        or not parts[1].isdigit()
        or not parts[2].isdigit()
    ):
        raise ValueError(f"잘못된 패턴 키 : {pattern_key}")

    size = int(parts[1])
    index = int(parts[2])

    if size <= 0 or index <= 0:
        raise ValueError(f"잘못된 패턴 키 : {pattern_key}")

    filter_key = f"size_{size}"
    filters = data["filters"][filter_key]

    return size, filters


def normalize_label(raw_label, label_type):
    mappings = {
        "expected": {
            "+": "Cross",
            "x": "X"
        },
        "filter": {
            "cross": "Cross",
            "x": "X"
        }
    }

    if label_type not in mappings:
        raise ValueError(f"알 수 없는 라벨 유형 : {label_type}")

    if not isinstance(raw_label, str):
        raise ValueError(f"문자열이 아닌 라벨 : {raw_label!r}")

    if raw_label not in mappings[label_type]:
        raise ValueError(
            f"지원하지 않는 {label_type} 라벨 : {raw_label!r}"
        )

    return mappings[label_type][raw_label]


def validate_matrix(matrix, size, label):
    if not isinstance(matrix, list):
        raise ValueError(
            f"{label} : 2차원 리스트가 아닙니다."
        )

    if len(matrix) != size:
        raise ValueError(
            f"{label} : 행 개수가 {size}개여야 합니다. "
            f"(현재 {len(matrix)}개)"
        )

    for row_number, row in enumerate(matrix, start=1):
        if not isinstance(row, list):
            raise ValueError(
                f"{label} : {row_number}행이 리스트가 아닙니다."
            )

        if len(row) != size:
            raise ValueError(
                f"{label} : {row_number}행의 열 개수가 "
                f"{size}개여야 합니다. (현재 {len(row)}개)"
            )

        for col_number, value in enumerate(row, start=1):
            if isinstance(value, bool) or not isinstance(
                value, (int, float)
            ):
                raise ValueError(
                    f"{label} : {row_number}행 {col_number}열에 "
                    "숫자가 아닌 값이 있습니다."
                )


def flatten_matrix(matrix):
    if not isinstance(matrix, list) or not matrix:
        raise ValueError(
            "행렬은 비어 있지 않은 2차원 리스트여야 합니다."
        )

    size = len(matrix)

    validate_matrix(matrix, size, "평탄화할 행렬")

    flatten = []

    for row in matrix:
        for value in row:
            flatten.append(value)

    return flatten


def calculate_mac_flat(pattern_flat, filter_flat):
    if (
        not isinstance(pattern_flat, list)
        or not isinstance(filter_flat, list)
    ):
        raise ValueError(
            "입력 패턴과 필터는 1차원 리스트여야 합니다."
        )

    if not pattern_flat or not filter_flat:
        raise ValueError(
            "입력 패턴과 필터는 비어 있을 수 없습니다."
        )

    if len(pattern_flat) != len(filter_flat):
        raise ValueError(
            "입력 패턴과 필터의 원소 개수가 같아야 합니다."
        )

    total = 0.0

    for index in range(len(pattern_flat)):
        total += pattern_flat[index] * filter_flat[index]

    return total


def compare_mac_performance(repetitions=1000):
    if (
        isinstance(repetitions, bool)
        or not isinstance(repetitions, int)
        or repetitions < 10
    ):
        raise ValueError(
            "반복 횟수는 10 이상의 정수여야 합니다."
        )

    def average_mac_ms(mac_function, input_data, filter_data):
        mac_function(input_data, filter_data)

        start_time = time.perf_counter()

        for _ in range(repetitions):
            mac_function(input_data, filter_data)

        end_time = time.perf_counter()

        return (end_time - start_time) * 1000 / repetitions

    results = []

    for size in (3, 5, 13, 25):
        filters_2d = {
            "Cross": generate_pattern(size, "Cross"),
            "X": generate_pattern(size, "X"),
        }

        filters_1d = {
            name: flatten_matrix(matrix)
            for name, matrix in filters_2d.items()
        }

        for pattern_type in ("Cross", "X"):
            pattern_2d = generate_pattern(size, pattern_type)
            pattern_1d = flatten_matrix(pattern_2d)

            for filter_type in ("Cross", "X"):
                filter_2d = filters_2d[filter_type]
                filter_1d = filters_1d[filter_type]

                score_2d = calculate_mac(
                    pattern_2d, filter_2d
                )

                score_1d = calculate_mac_flat(
                    pattern_1d, filter_1d
                )

                if score_2d != score_1d:
                    raise ValueError(
                     "2차원과 1차원 MAC 점수가 다릅니다."
                    )

                if len(results) % 2 == 0:
                    ms_2d = average_mac_ms(
                        calculate_mac, pattern_2d, filter_2d
                    )

                    ms_1d = average_mac_ms(
                        calculate_mac_flat, pattern_1d, filter_1d
                    )

                else:
                    ms_1d = average_mac_ms(
                        calculate_mac_flat, pattern_1d, filter_1d
                    )

                    ms_2d = average_mac_ms(
                        calculate_mac, pattern_2d, filter_2d
                    )

                results.append({
                    "size": size,
                    "mac_operations": size * size,
                    "pattern_type": pattern_type,
                    "filter_type": filter_type,
                    "score_2d": score_2d,
                    "score_1d": score_1d,
                    "average_2d_ms": ms_2d,
                    "average_1d_ms": ms_1d,
                    "repetitions": repetitions,
                })

    return results


def validate_json_case(data, pattern_key):
    if not isinstance(data, dict):
        raise ValueError("JSON 최상위 데이터가 객체가 아닙니다.")

    for required_key in ("filters", "patterns"):
        if required_key not in data:
            raise ValueError(
                f"JSON 필 수 키가 없습니다. : {required_key}"
            )

        if not isinstance(data[required_key], dict):
            raise ValueError(
                f"JSON의 {required_key}는 객체여야 합니다."
            )

    if not isinstance(pattern_key, str):
        raise ValueError("패턴 키는 문자열이어야 합니다.")

    if pattern_key not in data["patterns"]:
        raise ValueError(
            f"패턴을 찾을 수 없습니다. : {pattern_key}"
        )

    item = data["patterns"][pattern_key]

    if not isinstance(item, dict):
        raise ValueError(
            f"{pattern_key} : 패턴 데이터가 객체가 아닙니다."
        )

    for required_key in ("input", "expected"):
        if required_key not in item:
            raise ValueError(
                f"{pattern_key} : 필수 키가 없습니다. : {required_key}"
            )

    try:
        size, filters = select_filters_for_pattern(
            data, pattern_key
        )
    except KeyError as error:
        raise ValueError(
            f"{pattern_key} : 대응하는 크기의 필터가 없습니다."
        ) from error

    if not isinstance(filters, dict):
        raise ValueError(
            f"{pattern_key} : 필터 데이터가 객체가 아닙니다."
        )

    standard_filters = {}

    for filter_key in ("cross", "x"):
        if filter_key not in filters:
            raise ValueError(
                f"{pattern_key} : 필수 필터가 없습니다. : {filter_key}"
            )

        validate_matrix(
            filters[filter_key],
            size,
            f"{pattern_key}.{filter_key}"
        )

        standard_label = normalize_label(
            filter_key, "filter"
        )
        standard_filters[standard_label] = filters[filter_key]

    validate_matrix(
        item["input"],
        size,
        f"{pattern_key}.input"
    )

    expected_label = normalize_label(
        item["expected"], "expected"
    )

    return size, standard_filters, item["input"], expected_label


def prepare_json_case(data, pattern_key):
    try:
        prepared = validate_json_case(data, pattern_key)

    except (ValueError, KeyError, TypeError, IndexError) as error:
        error_reason = f"{type(error).__name__} : {error}"
        return None, error_reason

    return prepared, None


def analyze_json_case(data, pattern_key):
    prepared, error_reason = prepare_json_case(
        data, pattern_key
    )

    if error_reason is not None:
        return {
            "pattern_key": pattern_key,
            "size": None,
            "cross_score": None,
            "x_score": None,
            "expected": None,
            "actual": None,
            "status": "FAIL",
            "reason": error_reason,
        }

    size, filters, pattern, expected = prepared

    cross_score = calculate_mac(
        pattern, filters["Cross"]
    )

    x_score = calculate_mac(
        pattern, filters["X"]
    )

    actual = classify_scores(
        cross_score,
        x_score,
        label_a="Cross",
        label_b="X",
    )

    status = "PASS" if actual == expected else "FAIL"

    if status == "PASS":
        reason = None
    else:
        reason = (
            f"예상 정답 : {expected}, 실제 판정 : {actual}"
        )

    return {
        "pattern_key": pattern_key,
        "size": size,
        "cross_score": cross_score,
        "x_score": x_score,
        "expected": expected,
        "actual": actual,
        "status": status,
        "reason": reason,
    }


def analyze_all_json_cases(data):
    results = []

    for pattern_key in data["patterns"]:
        result = analyze_json_case(data, pattern_key)
        results.append(result)

    return results


def print_json_case_results(results):
    for result in results:
        print("-" * 50)

        print(f"CASE : {result['pattern_key']}")

        if result["size"] is None:
            print("SIZE : N/A")
        else:
            size = result["size"]
            print(f"SIZE : {size}x{size}")

        if result["cross_score"] is None:
            print("CROSS SCORE : N/A")
        else:
            print(f"CROSS SCORE : {result['cross_score']}")

        if result["x_score"] is None:
            print("X SCORE : N/A")
        else:
            print(f"X SCORE : {result['x_score']}")

        if result["expected"] is None:
            print("EXPECTED : N/A")
        else:
            print(f"EXPECTED : {result['expected']}")

        if result["actual"] is None:
            print("ACTUAL : N/A")
        else:
            print(f"ACTUAL : {result['actual']}")

        print(f"STATUS : {result['status']}")

        if result["reason"] is not None:
            print(f"REASON : {result['reason']}")

    if results:
        print("-" * 50)


def print_json_summary(results):
    total = len(results)
    pass_count = 0
    fail_count = 0

    for result in results:
        status = result["status"]

        if status == "PASS":
            pass_count += 1

        elif status == "FAIL":
            fail_count += 1

        else:
            raise ValueError(
                f"지원하지 않는 분석 상태 : {status}"
            )

    if total != pass_count + fail_count:
        raise ValueError(
            "전체 케이스 수와 PASS/FAIL 합계가 일치하지 않습니다."
        )

    print("=" * 50)
    print("JSON ANALYSIS SUMMARY")
    print(f"TOTAL CASES : {total}")
    print(f"PASS COUNT : {pass_count}")
    print(f"FAIL COUNT : {fail_count}")
    print("=" * 50)

    return {
        "total": total,
        "pass": pass_count,
        "fail": fail_count,
    }


def generate_pattern(size, pattern_type):
    if isinstance(size, bool) or not isinstance(size, int):
        raise ValueError("패턴 크기는 정수여야 합니다.")

    if size < 3 or size % 2 == 0:
        raise ValueError("패턴 크기는 3 이상의 홀수여야 합니다.")

    if pattern_type not in ("Cross", "X"):
        raise ValueError(
            f"지원하지 않는 패턴 유형 : {pattern_type}"
        )

    center = size // 2
    pattern = []

    for row in range(size):
        current_row = []

        for col in range(size):
            if pattern_type == "Cross":
                on_pattern = (
                    row == center or col == center
                )
            else:
                on_pattern = (
                    row == col or row + col == size - 1
                )

            current_row.append(
                1.0 if on_pattern else 0.0
            )

        pattern.append(current_row)

    return pattern


def read_or_generate_matrix(label, size=3):
    while True:
        print(f"\n[{label}] 입력 방식을 선택하세요.")
        print("1. 행렬 직접 입력")
        print("2. Cross(+) 패턴 자동 생성")
        print("3. X 패턴 자동 생성")

        choice = input("선택 (1/2/3) : ").strip()

        if choice == "1":
            return read_matrix(label, size)

        elif choice == "2":
            return generate_pattern(size, "Cross")

        elif choice == "3":
            return generate_pattern(size, "X")

        else:
            print("잘못된 선택입니다. 1, 2, 3 중에서 선택하세요.")


def main():
    print("=== Mini NPU Simulator ===")

    print("\n[1] 필터 입력")

    filter_a = read_or_generate_matrix("필터 A")
    filter_b = read_or_generate_matrix("필터 B")

    print("\n[저장 확인]")
    print(f"필터 A : {filter_a}")
    print(f"필터 B : {filter_b}")

    print("\n[2] 패턴 입력")

    pattern = read_or_generate_matrix("입력 패턴")

    score_a = calculate_mac(pattern, filter_a)
    score_b = calculate_mac(pattern, filter_b)

    result = classify_scores(score_a, score_b)

    print("\n[3] MAC 결과")
    print(f"A 점수 : {score_a}")
    print(f"B 점수 : {score_b}")

    if result == "UNDECIDED":
        print("판정 : 판정 불가 (UNDECIDED)")
    else:
        print(f"판정 : {result}")


if __name__ == "__main__":
    main()

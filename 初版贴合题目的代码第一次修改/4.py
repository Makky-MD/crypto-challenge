import os
import csv

def bin_to_hex(bin_str):
    """把空格分隔的二进制串转成8位十六进制（带0x前缀）"""
    full_bin = "".join(bin_str.split())
    full_bin = full_bin.ljust(32, '0')[:32]
    return "0x" + hex(int(full_bin, 2))[2:].zfill(8).upper()

def count_active_sboxes(bin_str):
    """统计活跃S盒数（每4位为一个S盒，非0则活跃）"""
    full_bin = "".join(bin_str.split())
    full_bin = full_bin.ljust(32, '0')[:32]
    count = 0
    for i in range(0, 32, 4):
        nibble = full_bin[i:i+4]
        if nibble != "0000":
            count += 1
    return count

def main():
    current_dir = os.getcwd()
    output_file = "all_paths_summary.csv"
    all_data = []

    for filename in os.listdir(current_dir):
        if filename.startswith("path_") and filename.endswith(".txt"):
            filepath = os.path.join(current_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            u_bin = None
            v_bin = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("Round 1:") or line.startswith("xin:"):
                    if ":" in line:
                        u_bin = line.split(":", 1)[1].strip()
                if line.startswith("xout:") and "=== Final Output ===" not in line:
                    v_bin = line.split(":", 1)[1].strip()
            
            if u_bin and v_bin:
                u_hex = bin_to_hex(u_bin)
                v_hex = bin_to_hex(v_bin)
                active_s = count_active_sboxes(v_bin)
                all_data.append({
                    "filename": filename,
                    "u": u_hex,
                    "v": v_hex,
                    "active_sboxes": active_s
                })

    # 写入CSV文件
    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["序号", "文件名", "输入掩码u", "输出掩码v", "活跃S盒数"])
        writer.writeheader()
        for idx, data in enumerate(all_data, 1):
            writer.writerow({
                "序号": idx,
                "文件名": data["filename"],
                "输入掩码u": data["u"],
                "输出掩码v": data["v"],
                "活跃S盒数": data["active_sboxes"]
            })

    print(f" 汇总完成！共处理{len(all_data)}个文件，结果已保存到 {output_file}")

if __name__ == "__main__":
    main()

import subprocess
import os
import sys

def run_spider(spider_dir, spider_name, output_file):
    print(f"\n{'='*50}")
    print(f"运行爬虫: {spider_name}")
    print(f"{'='*50}")
    
    cmd = f'scrapy crawl {spider_name} -o {output_file}'
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=spider_dir,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    rating_dir = os.path.join(base_dir, "ods爬虫生成", "rating")
    comment_dir = os.path.join(base_dir, "ods爬虫生成", "comment")
    
    rating_output = os.path.join(base_dir, "data","ODS_Resource_Data", "rating.json")
    comment_output = os.path.join(base_dir, "data", "ODS_Resource_Data", "comment.json")
    
    os.makedirs(os.path.join(base_dir, "data", "ODS_Resource_Data"), exist_ok=True)
    
    print("开始爬取数据...")
    print(f"输出目录: {os.path.join(base_dir, 'data', 'ODS_Resource_Data')}")
    
    success = True
    
    success = run_spider(rating_dir, "rate", rating_output) and success
    
    success = run_spider(comment_dir, "douban_comment", comment_output) and success
    
    print(f"\n{'='*50}")
    if success:
        print("所有爬虫运行完成！")
        print(f"评分数据: {rating_output}")
        print(f"评论数据: {comment_output}")
    else:
        print("部分爬虫运行失败，请检查错误信息")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
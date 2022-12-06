import pandas as pd
import numpy as np


def data_set():
    df = pd.read_csv("Groceries.csv")
    # 读取列数据
    col_2 = df['items']
    items = np.array(col_2)
    # 将列数据转化为二维数组
    list_t1 = []
    # line格式类似于{chicken,tropical fruit,other vegetables,vinegar,shopping bags}
    for line in items:
        line = line.strip('{').strip('}').split(',')
        s = []
        for i in line:
            s.append(i)
        list_t1.append(s)
    return list_t1


def create_c1(data):
    # 创建C1
    c1 = set()
    for items in data:
        for item in items:
            item_set = frozenset([item])
            c1.add(item_set)
    return c1


def is_apriori(ck_item, Lk):
    # 任何非频繁的(k-1)项集都不是频繁k项集的子集，因此Ck+1中每一个集合的子集都应该在Lk中
    for item in ck_item:
        sub_item = ck_item - frozenset([item])
        if sub_item not in Lk:
            return False
    return True


def create_ck(Lk, k):  # 通过合并Lk-1中前k-2项相同的项来获得Ck中的项
    Ck = set()
    len_Lk = len(Lk)
    list_Lk = list(Lk)
    for i in range(len_Lk):
        for j in range(i + 1, len_Lk):
            l1 = list(list_Lk[i])[0:k - 2]
            l2 = list(list_Lk[j])[0:k - 2]
            l1.sort()
            l2.sort()  # 为方便比较和后续操作，将前k-2项进行排序
            if l1 == l2:
                Ck_item = list_Lk[i] | list_Lk[j]
                if is_apriori(Ck_item, Lk):  # 舍弃非频繁项集
                    Ck.add(Ck_item)
    return Ck


def get_lk(data_set, Ck, threshold, support_data):
    # 计算出现次数
    # len:多维数组返回最外围的大小
    Lk = set()
    item_count = {}
    for t in data_set:
        for item in Ck:
            if item.issubset(t):
                if item not in item_count:
                    item_count[item] = 1
                else:
                    item_count[item] += 1  # 计算项集在所有购物篮中出现的次数
    for item in item_count:
        if item_count[item] >= threshold:
            Lk.add(item)
            support_data[item] = item_count[item] / data_num  # 不满足最小支持度丢弃
    return Lk


def get_rule(L, support_data, minconfidence):
    # 参数：所有的频繁项目集，项目集-支持度dic，最小置信度
    rule_list = []
    sub_set_list = []
    for i in range(len(L)):
        for frequent_set in L[i]:
            for sub_set in sub_set_list:
                if sub_set.issubset(frequent_set):  # 寻找上一轮循环中出现的frequent_set的子集
                    conf = support_data[frequent_set] / support_data[sub_set]  # conf(rule)=S(J)/S(J-j)
                    rule = (sub_set, frequent_set - sub_set, conf)
                    if conf >= minconfidence and rule not in rule_list:
                        rule_list.append(rule)
            sub_set_list.append(frequent_set)
    return rule_list


def create_c2(buckets, bit_list):  # 参数：buckets字典， bit_list列表
    c2 = set()
    for (k, v) in buckets.items():
        if bit_list[k] == 1:
            for pair in v:
                c2.add(frozenset([pair[0], pair[1]]))
    return c2


def generate_pairs(frequent_items, baskets):
    result = []
    frequent_item_processed = []    # avoid case like ab ba
    frequent_singletons = []
    for frequent_item in frequent_items:
        frequent_item = list(frequent_item)[0]
        frequent_singletons.append(frequent_item)
    for frequent_item in frequent_items:
        frequent_item = list(frequent_item)[0]
        ht = {}
        for basket in baskets:
            if len(basket) < 2:
                continue
            inside = True
            if frequent_item not in basket:
                inside = False
            if inside:
                for item in basket:
                    if (item not in frequent_singletons) or (item == frequent_item):
                        continue
                    ht.setdefault(item, 0)
        keys = ht.keys()
        for key in keys:
            tmp = [frequent_item]
            tmp.append(key)
            tmp.sort()
            if tmp not in result:
                result.append(tmp)
        frequent_item_processed.append(frequent_item)
    return result


def count_pairs(pairs, baskets):
    for pair in pairs:
        count = 0
        for basket in baskets:
            if len(basket) < 2:
                continue
            inside = True
            for i in range(len(pair)):
                if pair[i] not in basket:
                    inside = False
                    break
            if inside:
                count += 1
        pair.append(count)


def generate_bitmap(buckets, threshold):
    bitmap = 0
    for (k, v) in buckets.items():
        if v >= threshold:
            bitmap += 1 << k
    return bitmap


def bitmap_to_list(bitmap):
    bitmap_str = str(bin(bitmap))
    bucket_size = 2048
    str_len = len(bitmap_str)
    result = []
    for i in range(0, str_len - 2):
        digit = int(bitmap_str[str_len - 1 - i])
        result.append(digit)
    for i in range(0, bucket_size - (str_len - 2)):
        result.append(0)
    return result


if __name__ == "__main__":
    data = data_set()
    min_support = 0.005
    min_confidence = 0.5
    support_data = {}
    C1 = create_c1(data)
    # 计算threshold
    data_num = float(len(data))
    threshold = data_num * min_support
    L1 = get_lk(data, C1, threshold, support_data)
    print('L1共包含 %d 项' % (len(L1)))
    Lk = L1.copy()
    L = [Lk]
    buckets = {}
    pairs = generate_pairs(Lk, data)
    count_pairs(pairs, data)
    i = 0
    for pair in pairs:
        index = i % 2048
        buckets.setdefault(index, [])
        buckets[index].append(pair)
        i += 1
    bucket_count = {}
    for (k, v) in buckets.items():
        count = 0
        for item in v:
            count += item[2]
        bucket_count[k] = count
    bitmap = generate_bitmap(bucket_count, threshold)
    print(bin(bitmap))
    bit_list = bitmap_to_list(bitmap)
    c2 = create_c2(buckets, bit_list)
    Lk = get_lk(data, c2, threshold, support_data)
    print('L2共包含 %d 项' % (len(Lk)))
    Lk = Lk.copy()
    L.append(Lk)
    for k in range(3, 5):  # 3,4
        Ck = create_ck(Lk, k)
        Lk = get_lk(data, Ck, threshold, support_data)
        print('L%d共包含 %d 项' % (k, len(Lk)))
        Lk = Lk.copy()
        L.append(Lk)
    rule_list = get_rule(L, support_data, min_confidence)
    print('关联规则总数为 %d ' % (len(rule_list)))
    with open('L1.csv', 'w') as f:
        for key in L[0]:
            f.write('{},\t{}\n'.format(key, support_data[key]))
    with open('L2.csv', 'w') as f:
        for key in L[1]:
            f.write('{},\t{}\n'.format(key, support_data[key]))
    with open('L3.csv', 'w') as f:
        for key in L[2]:
            f.write('{},\t{}\n'.format(key, support_data[key]))
    with open('L4.csv', 'w') as f:
        for key in L[3]:
            f.write('{},\t{}\n'.format(key, support_data[key]))
    with open('rule.csv', 'w') as f:
        for item in rule_list:
            f.write('{}\t{}\t{}\t: {}\n'.format(item[0], "of", item[1], item[2]))

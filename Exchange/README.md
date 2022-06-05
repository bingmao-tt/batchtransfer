
## withdraw.csv

轉帳清單範例說明
|Currency|Address                                   |AddressTag|DisplayName|Amount|Note  |
|--------|------------------------------------------|----------|-----------|------|------|
|tt      |0x0000000000000000000000000000000000000001|tag01     |TT         |100001|note01|
|tt      |0x0000000000000000000000000000000000000002|tag02     |HECO       |50    |note02|
|tt      |0x0000000000000000000000000000000000000003|tag03     |TT         |50    |note03|
|usdt    |0x0000000000000000000000000000000000000004|tag04     |SOL        |150   |note04|
|ht      |0x0000000000000000000000000000000000000005|tag05     |HECO       |150   |note05|
|usdt    |0x0000000000000000000000000000000000000006|tag06     |ALGO       |50    |note06|
|husd    |0x0000000000000000000000000000000000000007|tag07     |HECO       |50    |note07|
|usdc    |0x0000000000000000000000000000000000000008|tag08     |BEP20      |150   |note08|
|husd    |0x0000000000000000000000000000000000000009|tag09     |ERC20      |150   |note09|

## config.json

設定檔參數說明

```
{
    "withdraw": false, //開啟轉帳. true:轉帳, false:不轉帳,單純測試和確認資訊
    "access_key": "", //火幣的access key
    "secret_key": "", //火幣的secret key
    "account_id": "", //帳號id,但目前用不到
    "withdraw_blank_time": true, //每筆轉帳是否需要隨機間隔時間
    "withdraw_blank_time_zero_fee": false, // 0 fee的轉帳(tt的話就是火幣帳號互轉)是否要等待時間
    "withdraw_blank_min_time": 1, //隨機等待時間最短幾秒
    "withdraw_blank_max_time": 3, //隨機等待時間最長幾秒
    "ignore_zero_amount": false, //要不要處理amount是0的轉帳, 目前還沒功用, 因為會在確認火幣最小轉帳金額時就被抓出來擋掉
    "check_withdraw_reuqest_interval": 5, //再轉帳狀態變成confirmed前, 要每多少秒確認一次
    "public_ip_url": "https://checkip.amazonaws.com/" //去那拿ip , https://checkip.amazonaws.com/ or http://ipgrab.io/ or https://ipecho.net/plain
}
```

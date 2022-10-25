const api = require('kucoin-futures-node-api')
const fs = require('fs');

// const config = {
//     apiKey: "633e67428209b100012a4ece",
//     secretKey: "40adac37-4cda-4dfe-bdc4-fa3bce439fd8",
//     passphrase: "dtNe6tF6Sy4PtXV",
//     environment: 'live'
// }

// const client = new api()
// client.init(config)
// a = "getOpenOrderStatistics"
// client[a]( {
// symbol: "XBTUSDTM"
// }).then((result) => {
//     console.log(result)
// }).catch((err) => {
// });

FAIL_COUNT_THRESHOLD = 0;

async function get_open_orders(name, apiKey, secretKey, passphrase, symbol) {
    params = {
        status: "open",
        symbol: symbol,
    }
    result = await run_kucoin_function(
        "getAccountOverview",
        params,
        apiKey,
        secretKey,
        passphrase
    );

    console.log(result);
    
    result.name =  name
    result.status =  "fail"
    result.symbol =  symbol
    return result
}

async function run_kucoin_function(
    kucoin_function,
    params,
    apiKey,
    secretKey,
    passphrase,
    fail_count = 0
) {
    const config = {
        apiKey: apiKey,
        secretKey: secretKey,
        passphrase: passphrase,
        environment: "live",
    };

    const client = new api();
    client.init(config);

    result = {
        status: "fail",
        msg: "no msg"
    };

    try {
        let r = await client[kucoin_function](params);
        result.code = r.code;

        if (r.code == "200000") {
            result.status = "success"
            result.data = r.data
        } else {
            console.log("HERE FAILED mf");
            console.log(r.data);
            result.msg = `[${r.code}] - ${r.data}`;
            result.status = "fail";
        }

        return result;
    } catch (err) {
        result.msg = "catch"
        if (err.response && err.response.status == 401) {
            result.msg = "[401] - " + err.response.data.msg;
            return result;
        } else if (err.response && err.response.status == 429) {
            result.msg = "[429] - Too many request";
            // await new Promise((r) => setTimeout(r, 100));
        } else if (err.response && err.response.status == 500) {
            result.msg = "[500] - Kucoin is down!!";
            // await new Promise((r) => setTimeout(r, 1000));
        } else {
            result.msg = `[Unknown Error] - ${err.message}`;
            console.error(result.msg);
            // console.log(`${err.response.statusText} : ${err.response.data.code} - ${err.response.data.msg}`)
        }

        if (fail_count < FAIL_COUNT_THRESHOLD) {
            console.log(`Retrying err: ${result.msg}`);
            return await run_kucoin_function(
                kucoin_function,
                params,
                apiKey,
                secretKey,
                passphrase,
                (fail_count = fail_count + 1)
            );
        }

        result.fail_count = fail_count;
        return result;
    }
}

async function bulk_config_and_get_open_orders(accounts, symbol) {
    promisees = accounts.map(account => {
        return get_open_orders(
            account.name,
            account.api_key,
            account.api_secret,
            account.api_passphrase,
            symbol,
        )
    });

    console.time(`Sent ${promisees.length} request in`)
    res = await Promise.all(promisees)
    console.log(`\n`)
    console.timeEnd(`Sent ${promisees.length} request in`)
    console.log(`\n`)
    return res
}

async function read_from_file_get_open_orders() {
    let raw_data = fs.readFileSync(__dirname+"/data/get_open_orders_in.json");
    let data = JSON.parse(raw_data);

    responses = await bulk_config_and_get_open_orders(
        data.accounts,
        data.side,
        data.symbol,
        data.type,
        data.leverage,
        data.size,
        data.price,
    )

    fs.writeFileSync(__dirname+"/data/get_open_orders_out.json", JSON.stringify(responses), "utf-8")
}

read_from_file_get_open_orders()
    
// bulk_config_and_get_open_orders(
//     accounts = [{
//         apiKey: "633e67428209b100012a4ece",
//         secretKey: "40adac37-4cda-4dfe-bdc4-fa3bce439fd8",
//         passphrase: "dtNe6tF6Sy4PtXV"
//     }],
//     symbol = "XBTUSDTM",
// ) 

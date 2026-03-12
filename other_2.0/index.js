const readline = require('readline');
const {
    automateTask,
    addNewAccount,
    getAccountList
} = require('./cookies_manager.js'); // 导入之前的代码

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

async function showMenu() {
    console.log('\n=== 淘宝账号管理系统 ===');
    console.log('1. 添加新账号');
    console.log('2. 查看所有账号');
    console.log('3. 使用指定账号登录');
    console.log('4. 退出');
    console.log('==================\n');

    rl.question('请选择操作 (1-4): ', async (choice) => {
        switch (choice) {
            case '1':
                rl.question('请输入新账号名称: ', async (accountName) => {
                    await addNewAccount(accountName);
                    showMenu();
                });
                break;

            case '2':
                const accounts = getAccountList();
                console.log('\n已保存的账号列表:');
                accounts.forEach((account, index) => {
                    console.log(`${index + 1}. ${account}`);
                });
                showMenu();
                break;

            case '3':
                const availableAccounts = getAccountList();
                if (availableAccounts.length === 0) {
                    console.log('没有保存的账号，请先添加账号！');
                    showMenu();
                    return;
                }
                console.log('\n可用账号:');
                availableAccounts.forEach((account, index) => {
                    console.log(`${index + 1}. ${account}`);
                });
                rl.question('请选择要使用的账号序号: ', async (index) => {
                    const accountName = availableAccounts[index - 1];
                    if (accountName) {
                        await automateTask(accountName);
                    } else {
                        console.log('无效的选择！');
                    }
                    showMenu();
                });
                break;

            case '4':
                rl.close();
                process.exit(0);
                break;

            default:
                console.log('无效的选择，请重新选择！');
                showMenu();
                break;
        }
    });
}

// 修改 cookies_manager.js 中的相关函数，确保它们可以被导出
module.exports = {
    automateTask,
    addNewAccount,
    getAccountList
};

// 启动程序
showMenu();

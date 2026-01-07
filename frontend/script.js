// 简单的登录功能（客户端侧验证）
document.getElementById('login-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // 简单的验证（实际应用中应与后端验证）
    if (username === 'admin' && password === 'password') {
        document.getElementById('login-section').classList.add('hidden');
        document.getElementById('main-section').classList.remove('hidden');
        document.getElementById('login-message').textContent = '';
    } else {
        document.getElementById('login-message').textContent = '用户名或密码错误';
        document.getElementById('login-message').style.color = 'red';
    }
});

// 查询功能
document.getElementById('query-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const query = document.getElementById('query').value;
    const image = document.getElementById('image').files[0];

    const formData = new FormData();
    formData.append('query', query);
    formData.append('user_id', 1); // 假设用户ID为1
    if (image) {
        formData.append('image', image);
    }

    try {
        const response = await fetch('/api/langgraph/query/query', {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': 'Basic ' + btoa('admin:your-swagger-password')
            }
        });

        if (response.ok) {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let result = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));
                        if (typeof data === 'string') {
                            result += data;
                        } else if (data.interruption) {
                            result += '\n[对话被中断]\n';
                        }
                    }
                }
            }

            document.getElementById('response').textContent = result;
        } else {
            document.getElementById('response').textContent = '查询失败: ' + response.statusText;
        }
    } catch (error) {
        document.getElementById('response').textContent = '查询错误: ' + error.message;
    }
});
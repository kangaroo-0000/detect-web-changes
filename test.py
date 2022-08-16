from opensearchpy import OpenSearch, RequestsHttpConnection
auth = ('admin', 'systex123!')
host = '10.11.233.105'
index_body = {
    'settings': {
        'index': {
            'number_of_shards': 4
        }
    }
}
test_dict = {'name': ['Beckham', 'Tony', 'Leo']}

client = OpenSearch(hosts=[{'host': host, 'port': 9200}], http_auth=auth, use_ssl=True,
                    verify_certs=False,
                    ssl_assert_hostname=False,
                    ssl_show_warn=False,
                    connection_class=RequestsHttpConnection)
# if not client.ping:
#     raise ValueError("Connection failed.")
# response = client.indices.create(index='test', ignore=400, body=index_body)
# print(response)
# client.index(index='test', body=test_dict)
print(client.count(index='test'))
response = client.search(index='test')
print(response)

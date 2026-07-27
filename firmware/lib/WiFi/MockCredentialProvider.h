#ifndef MOCK_CREDENTIAL_PROVIDER_H
#define MOCK_CREDENTIAL_PROVIDER_H

#include "ICredentialsProvider.h"

class MockCredentialProvider : public ICredentialsProvider {
public:
    MockCredentialProvider() {}
    ~MockCredentialProvider() override {}
    
    const char* getSSID() override { return "Home-WiFi"; }
    const char* getPassword() override { return "secretpass"; }
};

#endif

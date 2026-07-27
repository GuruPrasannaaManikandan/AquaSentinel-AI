#ifndef ICREDENTIALS_PROVIDER_H
#define ICREDENTIALS_PROVIDER_H

/**
 * @brief Abstract interface representing network credentials provider.
 */
class ICredentialsProvider {
public:
    virtual ~ICredentialsProvider() {}

    virtual const char* getSSID() = 0;
    virtual const char* getPassword() = 0;
};

#endif

#ifndef __FIBRE_POSIX_UDP_HPP
#define __FIBRE_POSIX_UDP_HPP

#include "posix_socket.hpp"

#include <netinet/in.h>

namespace fibre {

class PosixUdpRxChannel;
class PosixUdpTxChannel;

class PosixUdpRxChannel : public PosixSocketRXChannel {
    int init(int socket_id) = delete; // Use open() instead.
    int deinit() = delete; // Use close() instead.

public:
    /**
     * @brief Opens this channel for incoming UDP packets on the specified
     * local address.
     * 
     * The RX channel should eventually be closed using close().
     * 
     * @returns Zero on success or a non-zero error code otherwise.
     */
    int open(std::tuple<std::string, int> local_address);

    /**
     * @brief Opens this channel for incoming UDP packets using the same
     * underlying socket as the provided TX channel.
     * 
     * This will only succeed if the given TX channel is already open and has
     * been used at least once to send data. The local address of this RX
     * channel will be set to the same address and port that was used to send
     * the most recent UDP packet on the TX channel.
     * 
     * The RX channel should eventually be closed using close(). Doing so will
     * not affect the associated TX channel.
     * 
     * @param tx_channel: The TX channel based on which to initialized this RX
     *        channel.
     * @returns Zero on success or a non-zero error code otherwise.
     */
    int open(const PosixUdpTxChannel& tx_channel);

    /**
     * @brief Closes this channel.
     * This does not affect associated TX channels.
     */
    int close();
};

class PosixUdpTxChannel : public PosixSocketTXChannel {
    int init(int socket_id) = delete; // Use open() instead.
    int deinit() = delete; // Use close() instead.

public:
    /**
     * @brief Opens this channel for outgoing UDP packets to the specified
     * remote address.
     * 
     * The TX channel should eventually be closed using close().
     * 
     * @returns Zero on success or a non-zero error code otherwise.
     */
    int open(std::tuple<std::string, int> remote_address);

    /**
     * @brief Opens this channel for outgoing UDP packets using the same
     * underlying socket as the provied RX channel.
     * 
     * This will only succeed if the given RX channel is already open and has
     * received data at least once. The remote address of this TX channel will
     * be initialized to the origin of the most recently received packet on the
     * RX channel ("received" in this context means actually read by the client).
     * 
     * The TX channel should eventually be closed using close(). Doing so will
     * not affect the associated RX channel.
     * 
     * @param rx_channel: The RX channel based on which to initialized this TX
     *        channel.
     * @returns Zero on success or a non-zero error code otherwise.
     */
    int open(const PosixUdpRxChannel& rx_channel);

    /**
     * @brief Closes this channel.
     * This does not affect associated TX channels.
     */
    int close();
};

}

#endif // __FIBRE_POSIX_UDP_HPP
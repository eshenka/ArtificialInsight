fn main() {
    tonic_build::compile_protos("../proto/userdb.proto").unwrap();
}

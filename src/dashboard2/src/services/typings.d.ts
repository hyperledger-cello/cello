export namespace API {
  export interface Result<T> {
    status: string;
    msg: string;
    data: T;
  }
}
